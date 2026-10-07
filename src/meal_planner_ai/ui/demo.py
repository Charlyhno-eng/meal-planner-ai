"""Editable in-memory session data for the desktop application."""

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from pydantic import ValidationError
from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QGuiApplication

from meal_planner_ai.models.coordinator import (
    CoordinatorData,
    CoordinatorProposal,
    RequestedMeal,
    ShoppingItem,
)
from meal_planner_ai.models.planning import (
    PlanningProposal,
    PlanningSettings,
    validate_recipes,
)
from meal_planner_ai.storage.config import (
    load_glm_key,
    load_language,
    save_glm_key,
    save_language,
)
from meal_planner_ai.storage.coordinator import load_coordinator, save_coordinator
from meal_planner_ai.ui.assistant import PlanningAssistant
from meal_planner_ai.ui.i18n import ENGLISH, canonical_food, translate, translate_food
from meal_planner_ai.workflow.coordinator import build_coordinator_workflow

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
    """Editable session data with optional, explicitly requested local AI planning."""

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
        }
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
            "settings": self.settings,
            "coordinator": self._coordinator_data.model_dump(mode="json"),
            "pantry": [item.copy() for item in self._pantry],
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
        ]

    def _save_coordinator(self, data):
        if self._coordinator_error:
            raise ValueError(self._coordinator_error)
        if self._coordinator_path is not None:
            save_coordinator(self._coordinator_path, data)

    def apply_commands(self, proposal: CoordinatorProposal):
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
        for action in commands.actions:
            if action.service == "meal_request":
                data.meals.append(
                    RequestedMeal(
                        title=action.title,
                        servings=action.servings,
                        period=action.period,
                    )
                )
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
        if any(action.service == "pantry_set" for action in commands.actions):
            self._checked = {key for key in self._checked if key.startswith("request:")}
        self.changed.emit()

    @Slot(str, result=bool)
    def removeRequest(self, record_id):
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
        self._settings = proposal.settings.model_dump(mode="json")
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
        return self._settings.copy()

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
        return [
            dict(
                item,
                name=translate_food(item["name"], self._language),
                quantity=quantity_text(item["amount"], item["unit"], self._language),
            )
            for item in self._pantry
        ]

    def _eligible(self):
        excluded = [
            word.strip().casefold()
            for word in self._settings["dislikes"].split(",")
            if word.strip()
        ]
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
                }
                for name, amount, unit, _ in recipe["ingredients"]
            ],
        )

    @Property("QVariantList", notify=changed)
    def meals(self):
        return [self._meal(i) for i in range(len(self._plan))]

    @Property("QVariantList", notify=changed)
    def guests(self):
        return [self._meal(i) for i in self._guests if i < len(self._plan)]

    def _groceries(self):
        needed = defaultdict(float)
        categories = {}
        for index, recipe_id in enumerate(self._plan):
            servings = self._settings["people"] + self._guests.get(index, 0)
            for name, amount, unit, category in self.recipe_catalogue[recipe_id][
                "ingredients"
            ]:
                key = (name, unit)
                needed[key] += amount * servings
                categories[key] = category
        available = defaultdict(float)
        for item in self._pantry:
            available[(item["name"].casefold(), item["unit"])] += item["amount"]
        result = []
        for (name, unit), amount in needed.items():
            stock = available[(name.casefold(), unit)]
            remaining = max(0, amount - stock)
            key = f"{name}|{unit}"
            result.append(
                {
                    "id": key,
                    "name": self.translate(name),
                    "category": categories[(name, unit)],
                    "quantity": quantity_text(
                        remaining or amount, unit, self._language
                    ),
                    "available": remaining == 0,
                    "checked": key in self._checked,
                }
            )
        for item in self._coordinator_data.groceries:
            key = "request:" + item.id
            result.append(
                {
                    "id": key,
                    "requestId": item.id,
                    "name": translate_food(item.name, self._language),
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
    def configure(self, start, days, count, people, vegetarian, dislikes):
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
            )
        except ValidationError:
            self._notify(
                "Choisissez 1 à 14 jours, 1 à 28 repas et 1 à 12 personnes, "
                "avec une période valide."
            )
            return False
        previous = self._settings
        self._settings = settings.model_dump(mode="json")
        if self.recipe_catalogue and not self._eligible():
            self._settings = previous
            self._notify("Aucune recette ne correspond à ces préférences.")
            return False
        self._guests.clear()
        self._checked.clear()
        self._make_plan()
        self.changed.emit()
        self._notify("Paramètres du planning actualisés")
        return True

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

    @Slot(int, int)
    def setGuests(self, index, count):
        if not (0 <= index < len(self._plan) and 0 <= count <= 12):
            return
        if count:
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
