"""Adapt recipes from scoped constraints instead of stopping the meal workflow."""

from copy import deepcopy
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from test_bootstrap import visual_child

from src.agents.food_preferences import PreferenceConflict, check_preferences
from src.agents.intolerance_verification import IntoleranceConflict, check_intolerances
from src.agents.meal_planning import plan_meals
from src.domain.dietary import conflicting_terms
from src.models.coordinator import MealRequest, RequestedMeal
from src.models.household import excluded_terms
from src.models.recipes import Ingredient, Recipe
from src.ui import app
from src.ui.demo import DemoState
from src.workflow.meal_request import build_meal_workflow


def recipe(title="Dish", food="Riz", servings=2):
    return Recipe(
        title=title,
        servings=servings,
        subtitle="Adapted recipe",
        minutes=15,
        vegetarian=True,
        ingredients=[Ingredient(name=food, amount=100, unit="g", category="Épicerie")],
        steps=[f"Prepare {food}."],
    )


def requested(food="Riz"):
    return RequestedMeal(
        title="Dish",
        servings=2,
        period={"start": "2026-10-17", "end": "2026-10-17"},
        recipe=recipe(food=food),
    )


def meal_actions(count):
    return [
        dict(service="meal_request", title=f"Dish {i}", servings=2)
        for i in range(count)
    ]


def run_workflow(state, actions, respond, progress=None):
    return build_meal_workflow(
        coordinator_reason=lambda _: {"proposal": {"actions": actions}},
        recipe_reason=respond,
        progress=progress,
    ).invoke({"request": "Meals for the week", "context": state.planning_context()})[
        "result"
    ]


def guest_settings():
    return {
        "vegetarian": False,
        "dislikes": "champignons",
        "members": [{"name": "Alice", "intolerances": "oeufs"}],
        "guest_groups": [
            {
                "name": "Friends",
                "meals": [1],
                "members": [
                    {"name": "Bob", "intolerances": "gluten"},
                    {"name": "Eve", "intolerances": ""},
                ],
            },
            {
                "name": "Family",
                "meals": [1, 2],
                "members": [
                    {"name": "Jo", "intolerances": "lactose"},
                ],
            },
        ],
    }


@pytest.mark.parametrize("label", ["oeufs", "Œufs", "œuf", "Egg", "eggs", "OEUFS"])
@pytest.mark.parametrize("food", ["Œufs", "oeufs", "Eggs", "oeuf"])
def test_egg_spellings_and_languages_are_equivalent(label, food):
    assert conflicting_terms(food, excluded_terms({"dislikes": label}))


@pytest.mark.parametrize("food", ["Mushroom", "Champignon", "Champignons", "Mushrooms"])
def test_mushroom_spellings_are_equivalent(food):
    assert conflicting_terms(food, excluded_terms({"dislikes": "champignons"}))


def test_qualifiers_do_not_hide_ingredients_elsewhere():
    settings = {"dislikes": "gluten, oeufs", "vegetarian": False}
    meal = requested("Pâtes sans gluten")
    meal.recipe.title = "Gluten-free egg-free pasta"
    meal.recipe.subtitle = "Gluten-free pasta without eggs"
    check_preferences([meal], settings)
    check_intolerances([meal], meal.recipe.ingredients, settings)
    meal.recipe.ingredients.append(
        Ingredient(name="Eggs", amount=1, unit="pièce", category="Épicerie")
    )
    with pytest.raises(PreferenceConflict):
        check_preferences([meal], settings)
    with pytest.raises(IntoleranceConflict):
        check_intolerances([meal], [], settings)
    assert conflicting_terms("Pâtes sans gluten et pain", ["gluten", "oeufs"]) == [
        "pain"
    ]
    assert not conflicting_terms("pain d’épices", excluded_terms({"dislikes": "riz"}))


def test_guest_restrictions_union_only_for_matching_meals():
    settings = guest_settings()
    assert "gluten" not in excluded_terms(settings)
    assert "gluten" not in excluded_terms(settings, 0)
    assert "gluten" in excluded_terms(settings, 1)
    assert "lactose" in excluded_terms(settings, 1)
    assert "gluten" not in excluded_terms(settings, 2)
    assert "lactose" in excluded_terms(settings, 2)
    meal = requested("Bread")
    check_preferences([meal], settings, 0)
    check_preferences([meal], settings, 2)
    with pytest.raises(PreferenceConflict):
        check_preferences([meal], settings, 1)
    check_intolerances([meal], [], settings, 0)
    with pytest.raises(IntoleranceConflict):
        check_intolerances([meal], [], settings, 1)
    # Aggregated groceries include bread for a meal without the gluten-free guest.
    check_intolerances([], meal.recipe.ingredients, settings)


def test_planner_receives_explicit_constraints_before_first_generation(qt_app):
    context = DemoState().planning_context()
    context["settings"].update(guest_settings())
    context["planned_meal_count"] = 1
    seen = []

    def respond(payload):
        seen.append(payload)
        return {
            "recipes": [recipe(item["title"]).model_dump() for item in payload["meals"]]
        }

    plan_meals(
        [
            MealRequest(
                service="meal_request",
                title="Dish",
                servings=2,
                period={"start": "2026-10-17", "end": "2026-10-17"},
            )
        ],
        context,
        "",
        reason=respond,
    )
    rules = seen[0]["meal_constraints"][0]
    assert rules["meal_index"] == 1
    assert rules["excluded_foods"] == ["champignons", "oeufs", "gluten", "lactose"]
    assert "eggs" in rules["excluded_terms_and_sources"]
    assert "wheat" in rules["excluded_terms_and_sources"]
    assert [guest["name"] for guest in rules["guests"]] == ["Bob", "Eve", "Jo"]
    assert "guest_groups" not in seen[0]["settings"]


def test_only_incompatible_recipe_is_adapted_and_saved(qt_app, tmp_path):
    state = DemoState(config_path=tmp_path / "config.toml")
    assert state.setHousehold(
        [{"name": "Alice", "intolerances": "oeufs, champignons"}], False, ""
    )
    calls, progress = [], []
    actions = [
        dict(service="meal_request", title="Tiramisu", servings=6),
        dict(service="meal_request", title="Lasagnes", servings=2),
    ]

    def respond(payload):
        calls.append(deepcopy(payload))
        if len(calls) == 1:
            assert all(
                "oeufs" in rules["excluded_foods"][0]
                for rules in payload["meal_constraints"]
            )
            return {
                "recipes": [
                    recipe("Tiramisu", "Œufs", 6).model_dump(),
                    recipe("Lasagnes").model_dump(),
                ]
            }
        assert [meal["title"] for meal in payload["meals"]] == ["Tiramisu"]
        assert payload["validation_feedback"][0]["excluded_foods_found"]
        assert (
            payload["validation_feedback"][0]["rejected_recipe"]["ingredients"][0][
                "name"
            ]
            == "Œufs"
        )
        return {"recipes": [recipe("Tiramisu sans œufs", "Riz", 6).model_dump()]}

    before = state.planning_context()
    result = run_workflow(state, actions, respond, progress.append)
    assert state.planning_context() == before
    assert len(calls) == 2
    assert result.meals[0].title == "Tiramisu"
    assert result.meals[0].recipe.title == "Tiramisu sans œufs"
    assert any(step.startswith("Adaptation") for step in progress)
    assert result.meals[1].recipe.title == "Lasagnes"
    assert result.groceries[0].name == "Riz"
    state.apply_execution(result)
    assert state.meals[0]["title"] == "Tiramisu sans œufs"
    assert state.meals[0]["servings"] == 6
    assert DemoState(config_path=tmp_path / "config.toml").meals == state.meals


def test_week_keeps_gluten_except_at_guest_meal_and_append_offsets(qt_app, tmp_path):
    state = DemoState(config_path=tmp_path / "config.toml")
    profiles = [{"name": "Bob", "intolerances": "gluten"}, {"name": "Eve"}]
    assert state.addGuestGroup("Friends", [1], profiles)
    calls = []

    def respond(payload):
        calls.append(payload)
        return {
            "recipes": [
                recipe(
                    item["title"], "Pâtes sans gluten" if rules["guests"] else "Pâtes"
                ).model_dump()
                for item, rules in zip(
                    payload["meals"], payload["meal_constraints"], strict=True
                )
            ]
        }

    result = run_workflow(state, meal_actions(3), respond)
    assert [rules["excluded_foods"] for rules in calls[0]["meal_constraints"]] == [
        [],
        ["gluten"],
        [],
    ]
    assert [(item.name, item.required) for item in result.groceries] == [
        ("Pâtes", 200),
        ("Pâtes sans gluten", 200),
    ]
    state.apply_execution(result)
    assert [meal["servings"] for meal in state.meals] == [2, 4, 2]
    assert [meal["foodsToAvoid"] for meal in state.meals] == [[], ["gluten"], []]
    assert state.meals[1]["guestNames"] == ["Bob", "Eve"]
    assert state.addIngredientToGroceries(0, 0)
    assert state.groceries[0]["name"] == "Pâtes"
    second = run_workflow(state, meal_actions(1), respond)
    assert calls[1]["meal_constraints"][0]["meal_index"] == 3
    assert not calls[1]["meal_constraints"][0]["excluded_foods"]
    state.apply_execution(second)
    assert state.meals[3]["foodsToAvoid"] == []
    assert DemoState(config_path=tmp_path / "config.toml").meals == state.meals


def test_adding_guest_only_checks_the_selected_existing_meal(qt_app):
    state = DemoState()

    def respond(payload):
        return {
            "recipes": [
                recipe(item["title"], food).model_dump()
                for item, food in zip(payload["meals"], ["Pain", "Riz"], strict=True)
            ]
        }

    state.apply_execution(run_workflow(state, meal_actions(2), respond))
    assert state.addGuestGroup(
        "Friend", [1], [{"name": "Bob", "intolerances": "gluten"}]
    )
    before = state.planning_context()
    assert not state.addGuestGroup(
        "Other", [0], [{"name": "Eve", "intolerances": "gluten"}]
    )
    assert state.planning_context() == before


@pytest.mark.parametrize("language", ["fr", "en"])
def test_exhausted_adaptations_request_an_alternative_without_partial_save(
    qt_app, language
):
    state = DemoState()
    state.setLanguage(language)
    assert state.setHousehold([{"name": "Alice", "intolerances": "eggs"}], False, "")
    calls = []

    def respond(payload):
        calls.append(payload)
        return {
            "recipes": [
                recipe(item["title"], "Œufs").model_dump() for item in payload["meals"]
            ]
        }

    before = state.planning_context()
    result = run_workflow(state, meal_actions(1), respond)
    assert len(calls) == 3
    assert result.commands.clarification
    assert (
        "alternative dish" if language == "en" else "Quel autre plat"
    ) in result.commands.clarification
    assert result.meals == result.groceries == []
    assert state.planning_context() == before
    state.assistant._planned(result, "")
    assert not state.assistant.error
    assert state.assistant.reply == result.commands.clarification


def test_save_checks_current_scoped_guest_rules(qt_app):
    state = DemoState()
    result = run_workflow(
        state,
        meal_actions(1),
        lambda payload: {"recipes": [recipe("Dish 0", "Pain").model_dump()]},
    )
    assert state.addGuestGroup(
        "Friend", [0], [{"name": "Bob", "intolerances": "gluten"}]
    )
    before = state.planning_context()
    with pytest.raises(PreferenceConflict):
        state.apply_execution(result)
    assert state.planning_context() == before


@pytest.mark.parametrize("language", ["fr", "en"])
def test_interface_explains_meal_scopes(qt_app, tmp_path, language):
    state = DemoState(config_path=tmp_path / "config.toml")
    state.setLanguage(language)
    assert state.setHousehold([{"name": "Alice", "intolerances": "oeufs"}], False, "")
    assert state.addGuestGroup(
        "Friends", [1], [{"name": "Bob", "intolerances": "gluten"}]
    )
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(str(error) for error in errors)
    )
    engine.setInitialProperties({"demo": state})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    window = engine.rootObjects()[0]
    try:
        QTest.qWait(50)
        summary = visual_child(window.contentItem(), "householdDietarySummary")
        assert "oeufs" in summary.property("text")
        assert "gluten" not in summary.property("text")
        guests = visual_child(window.contentItem(), "guestDietarySummary-0")
        assert "Bob" in guests.property("text")
        assert "gluten" in guests.property("text")
        assert ("Repas 2" if language == "fr" else "Meal 2") in guests.property("text")
        state.apply_execution(
            run_workflow(
                state,
                meal_actions(2),
                lambda payload: {
                    "recipes": [
                        recipe(item["title"]).model_dump() for item in payload["meals"]
                    ]
                },
            )
        )
        dialog = window.findChild(QObject, "recipeDialog")
        dialog.setProperty("mealId", 1)
        QMetaObject.invokeMethod(dialog, "open")
        QTest.qWait(50)
        content = dialog.property("contentItem")
        assert "Bob" in visual_child(content, "recipeGuests").property("text")
        assert "gluten" in visual_child(content, "recipeExclusions").property("text")
        dialog.setProperty("mealId", 0)
        qt_app.processEvents()
        assert "gluten" not in visual_child(content, "recipeExclusions").property(
            "text"
        )
        assert not visual_child(content, "recipeGuests").property("visible")
        assert not warnings, "\n".join(warnings)
    finally:
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


def test_free_from_labels_do_not_override_disliked_foods():
    assert not conflicting_terms("Pâtes sans gluten", ["gluten"])
    assert conflicting_terms("Pâtes sans gluten", ["pâtes"])
    assert conflicting_terms("Pâtes sans gluten", ["gluten", "pâtes"])
    assert not conflicting_terms("Milk lactose-free", ["lactose"])
    assert conflicting_terms("Milk lactose-free", ["lactose", "milk"])


def test_repair_keeps_global_meal_index_after_an_existing_plan(qt_app, sample_session):
    state = DemoState()
    offset = len(state.meals)
    assert state.addGuestGroup(
        "Friend", [offset + 1], [{"name": "Bob", "intolerances": "gluten"}]
    )
    calls = []

    def respond(payload):
        calls.append(payload)
        food = "Pâtes" if len(calls) == 1 else "Riz"
        return {
            "recipes": [
                recipe(item["title"], food).model_dump() for item in payload["meals"]
            ]
        }

    result = run_workflow(state, meal_actions(3), respond)
    assert len(calls) == 2
    assert [rule["meal_index"] for rule in calls[1]["meal_constraints"]] == [offset + 1]
    assert calls[1]["meal_constraints"][0]["excluded_foods"] == ["gluten"]
    assert [meal["title"] for meal in calls[1]["meals"]] == ["Dish 1"]
    assert [meal.recipe.ingredients[0].name for meal in result.meals] == [
        "Pâtes",
        "Riz",
        "Pâtes",
    ]
    state.apply_execution(result)
    assert state.meals[offset]["guestNames"] == []
    assert state.meals[offset + 1]["guestNames"] == ["Bob"]


def test_catalogue_validation_and_replacement_use_meal_scope(qt_app, sample_session):
    from src.models.planning import PlanningProposal

    state = DemoState()
    # A future slot avoids conflicting with an already selected catalogue recipe.
    assert state.addGuestGroup(
        "Friend", [7], [{"name": "Bob", "intolerances": "gluten"}]
    )
    settings = state.settings
    settings["count"] = 8
    proposal = PlanningProposal(
        settings=settings,
        recipe_ids=[1, 0, 0, 0, 0, 0, 0, 0],
        pantry_updates=[],
        guests=[],
    )
    state.apply_proposal(proposal)
    assert state.meals[0]["foodsToAvoid"] == []
    assert state.meals[7]["foodsToAvoid"] == ["gluten"]
    assert 1 in state._eligible(0)
    assert 1 not in state._eligible(7)
    assert state.replaceMeal(7)
    assert state.meals[7]["art"] in state._eligible(7)
    proposal.recipe_ids[7] = 1
    before = state.planning_context()
    with pytest.raises(ValueError, match="excluded ingredient"):
        state.apply_proposal(proposal)
    assert state.planning_context() == before


def test_many_conflicts_still_produce_a_valid_clarification(qt_app):
    state = DemoState()
    assert state.setHousehold([{"name": "Alice", "intolerances": "eggs"}], False, "")
    actions = meal_actions(28)
    for action in actions:
        action["title"] = "Long requested dish " + "x" * 75

    def respond(payload):
        return {
            "recipes": [
                recipe(item["title"], "Eggs").model_dump() for item in payload["meals"]
            ]
        }

    result = run_workflow(state, actions, respond)
    assert result.commands.clarification
    assert len(result.commands.clarification) <= 1000
    assert result.meals == result.groceries == []
