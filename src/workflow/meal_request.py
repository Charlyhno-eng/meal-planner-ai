"""Desktop graph: coordinator → planning → preferences → groceries → verification.

All nodes work on a snapshot. Only the UI service persists a successful result.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.food_exclusion_verification import check_food_exclusions
from src.agents.food_preferences.agent import preference_conflicts
from src.agents.grocery_list import calculate_groceries
from src.agents.meal_planning import plan_meals
from src.domain.foods import canonical_food
from src.models.coordinator import CoordinatorProposal, RequestedMeal
from src.models.execution import MealExecution
from src.models.groceries import GroceryRequirement
from src.models.recipes import Ingredient
from src.ui.i18n import translate_food
from src.workflow.coordinator import build_coordinator_workflow


class MealWorkflowState(TypedDict, total=False):
    request: str
    context: dict
    conversation: list[dict]
    commands: CoordinatorProposal
    meals: list[RequestedMeal]
    groceries: list[GroceryRequirement]
    adaptation_attempts: int
    conflicts: list[dict]
    result: MealExecution


def execution_pantry(commands: CoordinatorProposal, context: dict) -> list[dict]:
    """Overlay absolute stock corrections before comparing recipe requirements."""
    pantry = [item.copy() for item in context["pantry"]]
    for action in commands.actions:
        if action.service != "pantry_set":
            continue
        food = action.model_dump(exclude={"service"})
        existing = next(
            (
                item
                for item in pantry
                if item["name"].casefold() == food["name"].casefold()
                and item["unit"] == food["unit"]
            ),
            None,
        )
        if existing is None:
            pantry.append(food)
        else:
            existing.update(food)
    return pantry


def calculate_execution_groceries(
    commands: CoordinatorProposal, meals: list[RequestedMeal], context: dict
) -> list[GroceryRequirement]:
    pantry = execution_pantry(commands, context)
    ingredients = [
        Ingredient.model_validate(item)
        for item in context.get("planned_ingredients", [])
    ]
    groups = context["settings"].get("guest_groups", [])
    for index, meal in enumerate(meals, context.get("planned_meal_count", 0)):
        guests = meal.guests + sum(
            len(group["members"]) for group in groups if index in group["meals"]
        )
        ingredients.extend(
            ingredient.model_copy(
                update={
                    "amount": ingredient.amount
                    * (meal.servings + guests)
                    / meal.recipe.servings
                }
            )
            for ingredient in meal.recipe.ingredients
        )
    return calculate_groceries(ingredients, pantry)


def build_meal_workflow(
    api_key: str = "", coordinator_reason=None, recipe_reason=None, progress=None
):
    report = progress or (lambda message: None)
    coordinator = build_coordinator_workflow(api_key, reason=coordinator_reason)

    def coordinate(state):
        report("GLM : envoi de votre demande et du contexte, attente de son analyse…")
        result = coordinator.invoke(state, {"recursion_limit": 60})
        report("GLM a répondu : votre demande a été structurée et validée.")
        return {
            "commands": result["proposal"],
            "meals": [],
            "groceries": [],
            "adaptation_attempts": 0,
            "conflicts": [],
        }

    def route(state):
        if state["commands"].clarification:
            return "finish"
        if any(a.service == "meal_request" for a in state["commands"].actions):
            return "meal_planning"
        return "grocery_list"

    def planning(state):
        report(
            "Planification : GLM prépare les recettes et les quantités pour vos repas…"
        )
        requests = [a for a in state["commands"].actions if a.service == "meal_request"]
        return {
            "meals": plan_meals(
                requests, state["context"], api_key, reason=recipe_reason
            )
        }

    def preferences(state):
        report(
            "Préférences : vérification des recettes et des aliments exclus du foyer…"
        )
        return {
            "conflicts": preference_conflicts(
                state["meals"],
                state["context"]["settings"],
                state["context"].get("planned_meal_count", 0),
            )
        }

    def preference_route(state):
        if not state["conflicts"]:
            return "grocery_list"
        return (
            "adapt_recipes" if state["adaptation_attempts"] < 2 else "ask_alternative"
        )

    def adapt(state):
        report(
            "Adaptation : remplacement des ingrédients incompatibles "
            "dans les repas concernés…"
        )
        offset = state["context"].get("planned_meal_count", 0)
        requests = [a for a in state["commands"].actions if a.service == "meal_request"]
        indices = [issue["meal_index"] for issue in state["conflicts"]]
        feedback = [
            dict(
                issue,
                rejected_recipe=state["meals"][
                    issue["meal_index"] - offset
                ].recipe.model_dump(),
            )
            for issue in state["conflicts"]
        ]
        repaired = plan_meals(
            [requests[index - offset] for index in indices],
            state["context"],
            api_key,
            reason=recipe_reason,
            meal_indices=indices,
            feedback=feedback,
        )
        meals = list(state["meals"])
        for index, meal in zip(indices, repaired, strict=True):
            meals[index - offset] = meal
        return {"meals": meals, "adaptation_attempts": state["adaptation_attempts"] + 1}

    def ask_alternative(state):
        vegetarian = (
            "vegetarian"
            if state["context"].get("language", "fr") == "en"
            else "végétarien"
        )
        details = "; ".join(
            f"{issue['meal_index'] + 1}: {issue['title']} "
            f"({', '.join(issue['excluded_foods_found']) or vegetarian})"
            for issue in state["conflicts"]
        )
        # Clarifications share the coordinator's 1,000-character limit, including
        # batches with many incompatible dishes or long food names.
        details = details[:500]
        question = (
            "I could not produce a compatible variant after two adaptations. "
            f"Meals to adapt: {details}. Which alternative dish would you like? "
            "Your food exclusions are kept. No changes have been saved."
            if state["context"].get("language", "fr") == "en"
            else "Je n’ai pas obtenu de variante compatible après deux adaptations. "
            f"Repas à adapter : {details}. Quel autre plat souhaitez-vous ? "
            "Vos exclusions sont conservées. Aucun changement n’a été enregistré."
        )
        return {
            "commands": CoordinatorProposal(clarification=question),
            "meals": [],
            "groceries": [],
        }

    def groceries(state):
        report(
            "Courses : calcul des besoins et déduction des quantités déjà en réserve…"
        )
        requirements = calculate_execution_groceries(
            state["commands"], state["meals"], state["context"]
        )
        pantry = execution_pantry(state["commands"], state["context"])
        ambiguous = [
            need
            for need in requirements
            if need.unit in ("g", "ml")
            and need.amount > 0
            and any(
                canonical_food(item["name"]).casefold() == need.name.casefold()
                and item["unit"] == "pièce"
                and item["amount"] > 0
                for item in pantry
            )
        ]
        if ambiguous:
            language = state["context"].get("language", "fr")
            foods = ", ".join(
                f"{translate_food(need.name, language)} ({need.required:g} {need.unit})"
                for need in ambiguous[:3]
            )
            question = (
                f"The recipes require {foods}, but your pantry lists these foods "
                "as pieces or packages. What is the weight or volume per package, "
                "or the total available in g or ml? No package size will be assumed."
                if language == "en"
                else f"Les recettes nécessitent {foods}, mais ces aliments sont "
                "en réserve "
                "en pièces ou en pots. Quel est le poids ou le volume par contenant, "
                "ou le total disponible en g ou ml ? Aucun format ne sera supposé."
            )
            return {
                "commands": CoordinatorProposal(clarification=question),
                "meals": [],
                "groceries": [],
            }
        return {"groceries": requirements}

    def verify_food_exclusions(state):
        report("Vérification : recettes et courses comparées aux aliments à éviter…")
        purchases = [
            action
            for action in state["commands"].actions
            if action.service == "grocery_add"
        ]
        check_food_exclusions(
            [
                RequestedMeal.model_validate(meal)
                for meal in state["context"].get("planned_meals", [])
            ],
            [],
            state["context"]["settings"],
            meal_offset=state["context"].get("catalogue_meal_count", 0),
        )
        check_food_exclusions(
            state["meals"],
            [*state["groceries"], *purchases],
            state["context"]["settings"],
            meal_offset=state["context"].get("planned_meal_count", 0),
        )
        return {}

    def finish(state):
        return {
            "result": MealExecution(
                commands=state["commands"],
                meals=state["meals"],
                groceries=state["groceries"],
            )
        }

    graph = StateGraph(MealWorkflowState)
    for name, node in (
        ("coordinator", coordinate),
        ("meal_planning", planning),
        ("food_preferences", preferences),
        ("adapt_recipes", adapt),
        ("ask_alternative", ask_alternative),
        ("grocery_list", groceries),
        ("food_exclusion_verification", verify_food_exclusions),
        ("finish", finish),
    ):
        graph.add_node(name, node)
    graph.add_edge(START, "coordinator")
    graph.add_conditional_edges("coordinator", route)
    graph.add_edge("meal_planning", "food_preferences")
    graph.add_conditional_edges("food_preferences", preference_route)
    graph.add_edge("adapt_recipes", "food_preferences")
    graph.add_edge("ask_alternative", "finish")
    graph.add_conditional_edges(
        "grocery_list",
        lambda state: (
            "finish"
            if state["commands"].clarification
            else "food_exclusion_verification"
        ),
    )
    graph.add_edge("food_exclusion_verification", "finish")
    graph.add_edge("finish", END)
    return graph.compile()
