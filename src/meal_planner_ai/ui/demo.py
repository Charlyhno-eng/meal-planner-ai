"""Desktop session services and persisted generated meals and purchases."""

from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path

from pydantic import ValidationError
from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QGuiApplication

from meal_planner_ai.agents.food_preferences import (
    PreferenceConflict,
    check_preferences,
)
from meal_planner_ai.agents.grocery_list import calculate_groceries
from meal_planner_ai.models.coordinator import (
    CoordinatorData,
    CoordinatorProposal,
    Period,
    RequestedMeal,
    ShoppingItem,
)
from meal_planner_ai.models.execution import MealExecution
from meal_planner_ai.models.household import Household, HouseholdMember, excluded_terms
from meal_planner_ai.models.planning import (
    PlanningProposal,
    PlanningSettings,
    validate_recipes,
)
from meal_planner_ai.models.recipes import Ingredient
from meal_planner_ai.storage.config import (
    load_glm_key,
    load_language,
    save_glm_key,
    save_language,
)
from meal_planner_ai.storage.coordinator import load_coordinator, save_coordinator
from meal_planner_ai.storage.household import load_household, save_household
from meal_planner_ai.ui.assistant import PlanningAssistant
from meal_planner_ai.ui.i18n import ENGLISH, canonical_food, translate, translate_food
from meal_planner_ai.workflow.coordinator import build_coordinator_workflow
from meal_planner_ai.workflow.meal_request import calculate_execution_groceries

MONTHS = [
    "janvier",
    "février",
    "mars",
    "avril",
    "mai",
    "juin",
    "juillet",
    "août",
    "septembre",
    "octobre",
    "novembre",
    "décembre",
]


def quantity_text(amount: float, unit: str, language: str = "fr") -> str:
    number = f"{amount:g}"
    if language == "fr":
        number = number.replace(".", ",")
    unit = translate(unit, language)
    return f"{number} {unit}{'s' if unit in ('pièce', 'piece') and amount > 1 else ''}"


class DemoState(QObject):
    """Editable household and stock data, with atomic agent-result application."""

    recipe_catalogue = []
    english_translations = ENGLISH

    changed = Signal()
    notice = Signal(str)

    def __init__(self, parent=None, config_path: Path | None = None):
        super().__init__(parent)
        self._config_path = config_path
        self._language = "fr"
        self._config_error = ""
        if config_path is not None:
            try:
                self._language = load_language(config_path)
            except (OSError, ValueError, TypeError, AttributeError):
                self._config_error = (
                    "Impossible de lire config.toml. Le français est utilisé."
                )
        self._glm_key = ""
        self._glm_error = ""
        self._glm_path = (
            config_path.with_name("glm-credentials.json") if config_path else None
        )
        if self._glm_path is not None:
            try:
                self._glm_key = load_glm_key(self._glm_path)
            except (OSError, ValueError, KeyError, TypeError):
                self._glm_error = "Impossible de lire la clé API GLM."
        self._settings = {
            "start": date.today().isoformat(),
            "days": 7,
            "count": 7,
            "people": 2,
            "vegetarian": False,
            "dislikes": "",
            "members": [{"name": "", "intolerances": ""} for _ in range(2)],
        }
        self._household_path = (
            config_path.parent / "data" / "household.json" if config_path else None
        )
        self._household_error = ""
        if self._household_path is not None:
            try:
                household = load_household(self._household_path)
                if household is not None:
                    self._settings.update(household.model_dump())
            except (OSError, ValueError):
                self._household_error = "Impossible de lire data/household.json."
        self._pantry = []
        self._next_id = 1
        self._plan = []
        self._guests = {}
        self._checked = set()
        self._coordinator_path = (
            config_path.parent / "data" / "coordinator.json" if config_path else None
        )
        self._coordinator_data = CoordinatorData()
        self._coordinator_error = ""
        if self._coordinator_path is not None:
            try:
                self._coordinator_data = load_coordinator(self._coordinator_path)
            except (OSError, ValueError):
                self._coordinator_error = (
                    "Impossible de lire data/coordinator.json. Corrigez le fichier "
                    "avant d’enregistrer de nouvelles demandes."
                )
        self._assistant = PlanningAssistant(self)

    @Property(QObject, constant=True)
    def assistant(self):
        return self._assistant

    def planning_context(self):
        return {
            "today": date.today().isoformat(),
            "language": self._language,
            "settings": self.settings,
            "coordinator": self._coordinator_data.model_dump(mode="json"),
            "pantry": [item.copy() for item in self._pantry],
            "planned_ingredients": [
                item.model_dump() for item in self._planned_ingredients()
            ],
            "guests": [
                {"meal": meal, "count": count} for meal, count in self._guests.items()
            ],
            "recipes": [
                dict(id=i, **{k: v for k, v in recipe.items() if k != "steps"})
                for i, recipe in enumerate(self.recipe_catalogue)
            ],
        }

    @Property(str, notify=changed)
    def coordinatorError(self):
        return self.translate(self._coordinator_error)

    @Property("QVariantList", notify=changed)
    def requestedMeals(self):
        return [
            dict(
                item.model_dump(mode="json"),
                periodLabel=(
                    f"{item.period.start.isoformat()} — {item.period.end.isoformat()}"
                ),
            )
            for item in self._coordinator_data.meals
            if item.recipe is None
        ]

    def _save_coordinator(self, data):
        if self._coordinator_error:
            raise ValueError(self._coordinator_error)
        if self._coordinator_path is not None:
            save_coordinator(self._coordinator_path, data)

    def _save_household(self, settings):
        if self._household_error:
            raise ValueError(self._household_error)
        household = Household.model_validate(
            {
                key: settings[key]
                for key in ("people", "members", "vegetarian", "dislikes")
            }
        )
        if self._household_path is not None:
            save_household(self._household_path, household)

    def apply_execution(self, execution: MealExecution):
        """Revalidate the complete batch before one atomic persistence operation."""
        execution = MealExecution.model_validate(execution.model_dump())
        if execution.commands.clarification:
            raise ValueError("A clarification cannot be applied")
        check_preferences(execution.meals, self._settings)
        expected = calculate_execution_groceries(
            execution.commands, execution.meals, self.planning_context()
        )
        if expected != execution.groceries:
            raise ValueError("Grocery requirements differ from the current plan")
        self.apply_commands(execution.commands, planned_meals=execution.meals)

    def apply_commands(self, proposal: CoordinatorProposal, planned_meals=None):
        # Validate again against the current household before staging any changes.
        result = build_coordinator_workflow(
            reason=lambda state: {"proposal": proposal}
        ).invoke({"context": self.planning_context()}, {"recursion_limit": 60})
        if result["proposal"].clarification:
            raise ValueError("A clarification cannot be applied")
        commands = CoordinatorProposal(actions=result["routed"])
        data = self._coordinator_data.model_copy(deep=True)
        pantry = [item.copy() for item in self._pantry]
        next_id = self._next_id
        planned = iter(planned_meals) if planned_meals is not None else None
        for action in commands.actions:
            if action.service == "meal_request":
                meal = (
                    next(planned)
                    if planned is not None
                    else RequestedMeal(
                        title=action.title,
                        servings=action.servings,
                        period=action.period,
                    )
                )
                data.meals.append(meal)
            elif action.service == "grocery_add":
                data.groceries.append(
                    ShoppingItem(**action.model_dump(exclude={"service"}))
                )
            elif action.service == "pantry_set":
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
                    pantry.append(dict(id=next_id, **food))
                    next_id += 1
                else:
                    existing.update(food)
        data = CoordinatorData.model_validate(data.model_dump())
        self._save_coordinator(data)
        self._coordinator_data = data
        self._pantry = pantry
        self._next_id = next_id
        if planned_meals or any(
            action.service == "pantry_set" for action in commands.actions
        ):
            self._checked = {key for key in self._checked if key.startswith("request:")}
        self.changed.emit()

    @Slot(str, result=bool)
    def removeRequest(self, record_id):
        removes_recipe = any(
            item.id == record_id and item.recipe is not None
            for item in self._coordinator_data.meals
        )
        data = self._coordinator_data.model_copy(deep=True)
        data.meals = [item for item in data.meals if item.id != record_id]
        data.groceries = [item for item in data.groceries if item.id != record_id]
        try:
            self._save_coordinator(data)
        except (ValueError, OSError):
            self._notify("Impossible d’enregistrer les demandes. Réessayez.")
            return False
        self._coordinator_data = data
        self._checked.discard("request:" + record_id)
        if removes_recipe:
            self._checked = {key for key in self._checked if key.startswith("request:")}
        self.changed.emit()
        return True

    def apply_proposal(self, proposal: PlanningProposal):
        """Validate everything before replacing data and recomputing groceries."""
        validate_recipes(proposal, self.recipe_catalogue, ENGLISH)
        pantry = [item.copy() for item in self._pantry]
        next_id = self._next_id
        seen = set()
        for update in proposal.pantry_updates:
            food = update.model_dump()
            food["name"] = canonical_food(food["name"].strip())
            key = (food["name"].casefold(), food["unit"])
            if not food["name"] or key in seen:
                raise ValueError("Empty or duplicate pantry update")
            seen.add(key)
            existing = next(
                (
                    item
                    for item in pantry
                    if (item["name"].casefold(), item["unit"]) == key
                ),
                None,
            )
            if existing is not None:
                existing.update(food)
            else:
                pantry.append(dict(id=next_id, **food))
                next_id += 1
        proposed = proposal.settings.model_dump(mode="json")
        if not proposed["members"]:
            proposed["members"] = [
                self._settings["members"][i]
                if i < len(self._settings["members"])
                else HouseholdMember().model_dump()
                for i in range(proposed["people"])
            ]
            validate_recipes(
                proposal.model_copy(update={"settings": PlanningSettings(**proposed)}),
                self.recipe_catalogue,
                ENGLISH,
            )
        self._save_household(proposed)
        self._settings = proposed
        self._plan = proposal.recipe_ids.copy()
        self._guests = {guest.meal: guest.count for guest in proposal.guests}
        self._pantry = pantry
        self._next_id = next_id
        self._checked.clear()
        self.changed.emit()

    def _notify(self, message):
        self.notice.emit(self.translate(message))

    @Property(str, notify=changed)
    def language(self):
        return self._language

    @Property(str, notify=changed)
    def configError(self):
        return self.translate(self._config_error)

    @Slot(str, result=str)
    def translate(self, text):
        return translate(text, self._language)

    @Slot(str, result=bool)
    def setLanguage(self, language):
        if language not in ("fr", "en"):
            return False
        try:
            if self._config_path is not None:
                save_language(self._config_path, language)
        except OSError:
            self._config_error = "Impossible d’enregistrer la langue dans config.toml."
            self.changed.emit()
            self._notify(self._config_error)
            return False
        self._language = language
        self._config_error = ""
        self.changed.emit()
        self._notify("Langue enregistrée")
        return True

    @Property(str, notify=changed)
    def glmApiKey(self):
        return self._glm_key

    @Property(str, notify=changed)
    def glmError(self):
        return self.translate(self._glm_error)

    @Slot(str, result=bool)
    def setGlmApiKey(self, key):
        key = key.strip()
        try:
            if self._glm_path is not None:
                save_glm_key(self._glm_path, key)
        except OSError:
            self._glm_error = "Impossible d’enregistrer la clé API GLM."
            self.changed.emit()
            return False
        self._glm_key = key
        self._glm_error = ""
        self.changed.emit()
        return True

    @Property("QVariantMap", notify=changed)
    def settings(self):
        return deepcopy(self._settings)

    @Property(str, notify=changed)
    def period(self):
        start = date.fromisoformat(self._settings["start"])
        end = start + timedelta(days=self._settings["days"] - 1)
        return (
            f"{start.day} {self.translate(MONTHS[start.month - 1])} — "
            f"{end.day} {self.translate(MONTHS[end.month - 1])}"
        )

    @Property("QVariantList", notify=changed)
    def pantry(self):
        usage = {
            (canonical_food(item.name).casefold(), item.unit): item.available
            for item in calculate_groceries(self._planned_ingredients(), self._pantry)
        }
        result = []
        for item in self._pantry:
            key = (canonical_food(item["name"]).casefold(), item["unit"])
            consumed = min(item["amount"], usage.get(key, 0))
            usage[key] = max(0, usage.get(key, 0) - consumed)
            remaining = max(0, item["amount"] - consumed)
            result.append(
                dict(
                    item,
                    name=translate_food(item["name"], self._language),
                    quantity=quantity_text(
                        item["amount"], item["unit"], self._language
                    ),
                    remainingAmount=remaining,
                    remainingQuantity=quantity_text(
                        remaining, item["unit"], self._language
                    ),
                )
            )
        return result

    def _eligible(self):
        excluded = excluded_terms(self._settings)
        return [
            i
            for i, recipe in enumerate(self.recipe_catalogue)
            if (not self._settings["vegetarian"] or recipe["vegetarian"])
            and not any(
                (
                    word in ingredient[0].casefold()
                    or word in ENGLISH.get(ingredient[0], ingredient[0]).casefold()
                )
                for word in excluded
                for ingredient in recipe["ingredients"]
            )
        ]

    def _make_plan(self):
        eligible = self._eligible()
        self._plan = (
            [eligible[i % len(eligible)] for i in range(self._settings["count"])]
            if eligible
            else []
        )

    def _meal(self, index):
        recipe = self.recipe_catalogue[self._plan[index]]
        guests = self._guests.get(index, 0)
        servings = self._settings["people"] + guests
        return dict(
            **{
                key: value
                for key, value in recipe.items()
                if key not in ("title", "subtitle", "steps", "ingredients")
            },
            title=self.translate(recipe["title"]),
            subtitle=self.translate(recipe["subtitle"]),
            steps=[self.translate(step) for step in recipe["steps"]],
            id=index,
            art=self._plan[index],
            label=f"{self.translate('Repas ')}{index + 1}",
            guests=guests,
            servings=servings,
            ingredients=[
                {
                    "name": self.translate(name),
                    "quantity": quantity_text(amount * servings, unit, self._language),
                    **self._ingredient_status(name, unit),
                }
                for name, amount, unit, _ in recipe["ingredients"]
            ],
        )

    def _generated_meals(self):
        return [
            item for item in self._coordinator_data.meals if item.recipe is not None
        ]

    def _generated_meal(self, item, index):
        recipe = item.recipe
        servings = item.servings + item.guests
        return dict(
            id=len(self._plan) + index,
            requestId=item.id,
            title=recipe.title,
            subtitle=recipe.subtitle,
            minutes=recipe.minutes,
            vegetarian=recipe.vegetarian,
            color="#cdb781",
            art=index,
            label=f"{self.translate('Repas ')}{len(self._plan) + index + 1}",
            servings=servings,
            baseServings=item.servings,
            guests=item.guests,
            periodLabel=(
                f"{item.period.start.isoformat()} — {item.period.end.isoformat()}"
            ),
            steps=recipe.steps,
            ingredients=[
                {
                    "name": translate_food(ingredient.name, self._language),
                    **self._ingredient_status(ingredient.name, ingredient.unit),
                    "quantity": quantity_text(
                        ingredient.amount * servings / recipe.servings,
                        ingredient.unit,
                        self._language,
                    ),
                }
                for ingredient in recipe.ingredients
            ],
        )

    @Property("QVariantList", notify=changed)
    def meals(self):
        return [self._meal(i) for i in range(len(self._plan))] + [
            self._generated_meal(item, i)
            for i, item in enumerate(self._generated_meals())
        ]

    @Property("QVariantList", notify=changed)
    def guests(self):
        return [meal for meal in self.meals if meal["guests"]]

    def _planned_ingredients(self):
        ingredients = []
        for index, recipe_id in enumerate(self._plan):
            servings = self._settings["people"] + self._guests.get(index, 0)
            for name, amount, unit, category in self.recipe_catalogue[recipe_id][
                "ingredients"
            ]:
                ingredients.append(
                    Ingredient(
                        name=name,
                        amount=amount * servings,
                        unit=unit,
                        category=category,
                    )
                )
        for meal in self._generated_meals():
            for ingredient in meal.recipe.ingredients:
                ingredients.append(
                    ingredient.model_copy(
                        update={
                            "amount": ingredient.amount
                            * (meal.servings + meal.guests)
                            / meal.recipe.servings
                        }
                    )
                )
        return ingredients

    def _ingredient_status(self, name, unit):
        key = (canonical_food(name).casefold(), unit)
        requirement = next(
            item
            for item in calculate_groceries(self._planned_ingredients(), self._pantry)
            if (canonical_food(item.name).casefold(), item.unit) == key
        )
        purchases = sum(
            item["amount"]
            for item in self._groceries()
            if not item["available"]
            and (canonical_food(item["foodName"]).casefold(), item["unit"]) == key
        )
        missing = max(0, requirement.amount - purchases)
        return dict(
            inPantry=requirement.amount == 0,
            inGroceries=requirement.amount > 0 and missing < 1e-9,
            missingAmount=missing,
        )

    @Slot(int, int, result=bool)
    def addIngredientToGroceries(self, meal_id, ingredient_index):
        if not 0 <= meal_id < len(self.meals):
            return False
        if meal_id < len(self._plan):
            recipe = self.recipe_catalogue[self._plan[meal_id]]
            ingredients = [
                Ingredient(name=n, amount=a, unit=u, category=c)
                for n, a, u, c in recipe["ingredients"]
            ]
            start = date.fromisoformat(self._settings["start"])
            period = Period(
                start=start, end=start + timedelta(days=self._settings["days"] - 1)
            )
        else:
            meal = self._generated_meals()[meal_id - len(self._plan)]
            ingredients = meal.recipe.ingredients
            period = meal.period
        if not 0 <= ingredient_index < len(ingredients):
            return False
        ingredient = ingredients[ingredient_index]
        missing = self._ingredient_status(ingredient.name, ingredient.unit)[
            "missingAmount"
        ]
        if missing < 1e-9:
            return True
        data = self._coordinator_data.model_copy(deep=True)
        try:
            data.groceries.append(
                ShoppingItem(
                    name=canonical_food(ingredient.name),
                    amount=float(missing),
                    unit=ingredient.unit,
                    category=ingredient.category,
                    period=period,
                )
            )
            data = CoordinatorData.model_validate(data.model_dump())
            self._save_coordinator(data)
        except (ValueError, OSError):
            self._notify("Impossible d’enregistrer les demandes. Réessayez.")
            return False
        self._coordinator_data = data
        self.changed.emit()
        return True

    def _groceries(self):
        result = []
        for item in self._coordinator_data.groceries:
            key = "request:" + item.id
            result.append(
                {
                    "id": key,
                    "requestId": item.id,
                    "name": translate_food(item.name, self._language),
                    "foodName": item.name,
                    "unit": item.unit,
                    "amount": item.amount,
                    "category": item.category,
                    "quantity": quantity_text(item.amount, item.unit, self._language),
                    "available": False,
                    "checked": key in self._checked,
                    "periodLabel": (
                        f"{item.period.start.isoformat()}"
                        f" — {item.period.end.isoformat()}"
                    ),
                }
            )
        return sorted(result, key=lambda item: (item["category"], item["name"]))

    @Property("QVariantList", notify=changed)
    def groceries(self):
        return self._groceries()

    @Slot(str, int, int, int, bool, str, result=bool)
    def configure(self, start, days, count, people, vegetarian, dislikes, members=None):
        try:
            date.fromisoformat(start)
        except ValueError:
            self._notify("Saisissez une date valide : AAAA-MM-JJ.")
            return False
        try:
            settings = PlanningSettings(
                start=start,
                days=days,
                count=count,
                people=people,
                vegetarian=vegetarian,
                dislikes=dislikes.strip(),
                members=(
                    members
                    if members is not None
                    else [
                        self._settings["members"][i]
                        if i < len(self._settings["members"])
                        else HouseholdMember().model_dump()
                        for i in range(max(0, min(people, 12)))
                    ]
                ),
            )
        except ValidationError:
            self._notify(
                "Choisissez 1 à 14 jours, 1 à 28 repas et 1 à 12 personnes, "
                "avec une période valide."
            )
            return False
        try:
            check_preferences(self._generated_meals(), settings.model_dump())
        except PreferenceConflict as exc:
            self._notify(str(exc))
            return False
        previous = self._settings
        self._settings = settings.model_dump(mode="json")
        if self.recipe_catalogue and not self._eligible():
            self._settings = previous
            self._notify("Aucune recette ne correspond à ces préférences.")
            return False
        try:
            self._save_household(self._settings)
        except (OSError, ValueError):
            self._settings = previous
            self._notify("Impossible d’enregistrer le foyer. Réessayez.")
            return False
        self._guests.clear()
        self._checked.clear()
        self._make_plan()
        self.changed.emit()
        self._notify("Paramètres du planning actualisés")
        return True

    @Property(str, notify=changed)
    def householdError(self):
        return self.translate(self._household_error)

    @Slot("QVariantList", bool, str, result=bool)
    def setHousehold(self, members, vegetarian, dislikes):
        return self.configure(
            self._settings["start"],
            self._settings["days"],
            self._settings["count"],
            len(members),
            vegetarian,
            dislikes,
            members=members,
        )

    @Slot(int, result=bool)
    def replaceMeal(self, index):
        if not 0 <= index < len(self._plan):
            return False
        eligible = self._eligible()
        if len(eligible) < 2:
            self._notify("Aucune autre recette disponible.")
            return False
        current = eligible.index(self._plan[index])
        self._plan[index] = eligible[(current + 1) % len(eligible)]
        self._checked.clear()
        self.changed.emit()
        self._notify("Repas remplacé · courses actualisées")
        return True

    @Slot(int, str, float, str, str, result=bool)
    def saveFood(self, item_id, name, amount, unit, category):
        name = canonical_food(name.strip())
        if not name or not (0 < amount <= 100000) or unit not in ("g", "ml", "pièce"):
            self._notify("Ajoutez un nom et une quantité supérieure à zéro.")
            return False
        if category not in ("Fruits & légumes", "Épicerie", "Produits frais"):
            return False
        item = dict(id=item_id, name=name, amount=amount, unit=unit, category=category)
        if item_id < 0:
            item["id"] = self._next_id
            self._next_id += 1
            self._pantry.append(item)
        else:
            for i, existing in enumerate(self._pantry):
                if existing["id"] == item_id:
                    self._pantry[i] = item
                    break
            else:
                return False
        self._checked.clear()
        self.changed.emit()
        self._notify("Réserve actualisée")
        return True

    @Slot(int)
    def removeFood(self, item_id):
        self._pantry = [item for item in self._pantry if item["id"] != item_id]
        self._checked.clear()
        self.changed.emit()
        self._notify("Aliment retiré")

    @Slot(int, int, result=bool)
    def setMealServings(self, index, servings):
        if not (len(self._plan) <= index < len(self.meals) and 1 <= servings <= 32):
            return False
        item = self._generated_meals()[index - len(self._plan)]
        data = self._coordinator_data.model_copy(deep=True)
        meal = next(meal for meal in data.meals if meal.id == item.id)
        ratio = servings / meal.recipe.servings
        meal.recipe.ingredients = [
            ingredient.model_copy(update={"amount": ingredient.amount * ratio})
            for ingredient in meal.recipe.ingredients
        ]
        meal.servings = servings
        meal.recipe.servings = servings
        try:
            data = CoordinatorData.model_validate(data.model_dump())
            self._save_coordinator(data)
        except (ValueError, OSError):
            self._notify("Impossible d’enregistrer les demandes. Réessayez.")
            return False
        self._coordinator_data = data
        self.changed.emit()
        return True

    @Slot(int, int)
    def setGuests(self, index, count):
        if not (0 <= index < len(self.meals) and 0 <= count <= 12):
            return
        if index >= len(self._plan):
            item = self._generated_meals()[index - len(self._plan)]
            data = self._coordinator_data.model_copy(deep=True)
            next(meal for meal in data.meals if meal.id == item.id).guests = count
            try:
                self._save_coordinator(data)
            except (ValueError, OSError):
                self._notify("Impossible d’enregistrer les demandes. Réessayez.")
                return
            self._coordinator_data = data
        elif count:
            self._guests[index] = count
        else:
            self._guests.pop(index, None)
        self._checked.clear()
        self.changed.emit()
        self._notify("Invités actualisés · portions ajustées")

    @Slot(str)
    def toggleGrocery(self, key):
        if key in self._checked:
            self._checked.remove(key)
        else:
            self._checked.add(key)
        self.changed.emit()

    @Slot()
    def copyGroceries(self):
        lines = [
            f"{'✓' if item['checked'] else '☐'} {item['name']} — {item['quantity']}"
            + (f" ({item['periodLabel']})" if item.get("periodLabel") else "")
            for item in self._groceries()
            if not item["available"]
        ]
        QGuiApplication.clipboard().setText(
            self.translate("Courses") + "\n" + "\n".join(lines)
        )
        self._notify("Liste copiée dans le presse-papiers")
