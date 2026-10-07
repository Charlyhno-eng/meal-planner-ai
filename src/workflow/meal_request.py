"""Desktop graph: coordinator → meal planning → preferences → groceries.

All nodes work on a snapshot. Only the UI service persists a successful result.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.food_preferences import check_preferences
from src.agents.grocery_list import calculate_groceries
from src.agents.meal_planning import plan_meals
from src.models.coordinator import CoordinatorProposal, RequestedMeal
from src.models.execution import MealExecution
from src.models.groceries import GroceryRequirement
from src.models.recipes import Ingredient
from src.workflow.coordinator import build_coordinator_workflow


class MealWorkflowState(TypedDict, total=False):
    request: str
    context: dict
    conversation: list[dict]
    commands: CoordinatorProposal
    meals: list[RequestedMeal]
    groceries: list[GroceryRequirement]
    result: MealExecution


def calculate_execution_groceries(
    commands: CoordinatorProposal, meals: list[RequestedMeal], context: dict
) -> list[GroceryRequirement]:
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
    ingredients = [
        Ingredient.model_validate(item)
        for item in context.get("planned_ingredients", [])
    ]
    for meal in meals:
        ingredients.extend(meal.recipe.ingredients)
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
        return {"commands": result["proposal"], "meals": [], "groceries": []}

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
        check_preferences(state["meals"], state["context"]["settings"])
        return {}

    def groceries(state):
        report(
            "Courses : calcul des besoins et déduction des quantités déjà en réserve…"
        )
        return {
            "groceries": calculate_execution_groceries(
                state["commands"], state["meals"], state["context"]
            )
        }

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
        ("grocery_list", groceries),
        ("finish", finish),
    ):
        graph.add_node(name, node)
    graph.add_edge(START, "coordinator")
    graph.add_conditional_edges("coordinator", route)
    graph.add_edge("meal_planning", "food_preferences")
    graph.add_edge("food_preferences", "grocery_list")
    graph.add_edge("grocery_list", "finish")
    graph.add_edge("finish", END)
    return graph.compile()
