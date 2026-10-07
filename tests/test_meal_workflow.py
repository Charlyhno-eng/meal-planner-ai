"""Complete desktop agent chain, live progress and atomic automatic application."""

import io
import json
from contextlib import contextmanager
from threading import Event

import pytest
from pydantic import ValidationError
from PySide6.QtTest import QTest

from meal_planner_ai.agents.food_preferences import PreferenceConflict
from meal_planner_ai.models.coordinator import CoordinatorProposal, Period
from meal_planner_ai.providers.glm import CoordinatorUnavailable
from meal_planner_ai.ui.demo import DemoState
from meal_planner_ai.workflow.coordinator import resolve_period
from meal_planner_ai.workflow.meal_request import build_meal_workflow


def meal_action(**changes):
    return dict(
        service="meal_request",
        title="Tiramisu",
        servings=2,
        period="this_week",
        **changes,
    )


def result_for(state, fake_recipes, actions=None, progress=None):
    actions = actions or [meal_action()]
    graph = build_meal_workflow(
        coordinator_reason=lambda state: {"proposal": {"actions": actions}},
        recipe_reason=lambda payload: fake_recipes("", payload, "test-key"),
        progress=progress,
    )
    return graph.invoke(
        {
            "request": "J’ai envie de faire un tiramisu cette semaine",
            "context": state.planning_context(),
        }
    )["result"]


def wait_for_job(assistant):
    for _ in range(200):
        QTest.qWait(10)
        if not assistant.busy:
            return
    pytest.fail("Agent job did not finish")


def test_graph_separates_agents_and_subtracts_stock(qt_app, fake_recipes):
    state = DemoState()
    state.saveFood(-1, "Mascarpone", 60, "g", "Produits frais")
    before = state.planning_context()
    steps = []
    result = result_for(state, fake_recipes, progress=steps.append)
    assert state.planning_context() == before
    assert len(result.meals) == 1
    meal = result.meals[0]
    assert meal.recipe.title == "Tiramisu"
    assert meal.recipe.servings == 2
    assert meal.period.start.weekday() == 0
    mascarpone = next(item for item in result.groceries if item.name == "Mascarpone")
    assert (mascarpone.required, mascarpone.available, mascarpone.amount) == (
        100,
        60,
        40,
    )
    assert len(steps) == 5
    assert steps[0].startswith("GLM : envoi")
    assert steps[1].startswith("GLM a répondu")
    assert steps[2].startswith("Planification")
    assert steps[3].startswith("Préférences")
    assert steps[4].startswith("Courses")
    state.apply_execution(result)
    assert state.meals[0]["title"] == "Tiramisu"
    assert state.requestedMeals == []
    assert state.pantry[0]["amount"] == 60  # Planning does not consume stock.


def test_compound_request_uses_declared_stock_and_shares_it_once(qt_app, fake_recipes):
    state = DemoState()
    actions = [
        meal_action(),
        meal_action(),
        {
            "service": "pantry_set",
            "name": "Mascarpone",
            "amount": 150,
            "unit": "g",
            "category": "Produits frais",
        },
    ]
    result = result_for(state, fake_recipes, actions=actions)
    item = next(item for item in result.groceries if item.name == "Mascarpone")
    assert (item.required, item.available, item.amount) == (200, 150, 50)
    state.apply_execution(result)
    assert len(state.meals) == 2
    assert state.groceries == []
    assert state.meals[0]["ingredients"][0]["missingAmount"] == 50
    assert state.addIngredientToGroceries(0, 0)
    assert state.groceries[0]["quantity"] == "50 g"


@pytest.mark.parametrize("excluded", ["mascarpone", "Sucre", "sugar"])
def test_excluded_ingredient_rejects_entire_batch(qt_app, fake_recipes, excluded):
    state = DemoState()
    state.configure("2026-10-07", 7, 7, 2, False, excluded)
    before = state.planning_context()
    with pytest.raises(PreferenceConflict, match="aliment exclu"):
        result_for(state, fake_recipes)
    assert state.planning_context() == before
    assert state.meals == state.groceries == []


@pytest.mark.parametrize(
    "change",
    [
        {"servings": 3},
        {"title": "A different meal"},
        {"ingredients": []},
        {"steps": [" "]},
        {
            "ingredients": [
                {"name": "Sucre", "amount": -10, "unit": "g", "category": "Épicerie"}
            ]
        },
    ],
)
def test_invalid_recipe_never_changes_session(qt_app, fake_recipes, change):
    state = DemoState()
    before = state.planning_context()

    def invalid(payload):
        batch = json.loads(fake_recipes("", payload, "key"))
        batch["recipes"][0].update(change)
        return batch

    graph = build_meal_workflow(
        coordinator_reason=lambda state: {"proposal": {"actions": [meal_action()]}},
        recipe_reason=invalid,
    )
    with pytest.raises((ValidationError, ValueError)):
        graph.invoke({"request": "Tiramisu", "context": before})
    assert state.planning_context() == before


def test_vegetarian_setting_is_checked_after_generation(qt_app, fake_recipes):
    state = DemoState()
    state.configure("2026-10-07", 7, 7, 2, True, "")

    def incompatible(payload):
        batch = json.loads(fake_recipes("", payload, "key"))
        batch["recipes"][0]["vegetarian"] = False
        return batch

    graph = build_meal_workflow(
        coordinator_reason=lambda state: {"proposal": {"actions": [meal_action()]}},
        recipe_reason=incompatible,
    )
    with pytest.raises(PreferenceConflict, match="végétarien"):
        graph.invoke({"request": "Tiramisu", "context": state.planning_context()})
    assert state.meals == []


def test_piece_shortfalls_round_up_and_units_remain_distinct(qt_app):
    from meal_planner_ai.agents.grocery_list import calculate_groceries
    from meal_planner_ai.models.recipes import Ingredient

    needs = [
        Ingredient(name="Œufs", amount=2.5, unit="pièce", category="Produits frais")
    ]
    result = calculate_groceries(
        needs,
        [
            {"name": "Eggs", "amount": 1, "unit": "pièce"},
            {"name": "Œufs", "amount": 100, "unit": "g"},
        ],
    )
    assert result[0].available == 1
    assert result[0].amount == 2


def test_saved_recipes_restore_and_guests_update_groceries(
    qt_app, tmp_path, fake_recipes
):
    path = tmp_path / "config.toml"
    state = DemoState(config_path=path)
    state.apply_execution(result_for(state, fake_recipes))
    assert state.groceries == []
    assert state.addIngredientToGroceries(0, 0)
    assert state.groceries[0]["amount"] == 100
    state.setGuests(0, 2)
    assert state.groceries[0]["amount"] == 100
    assert state.meals[0]["ingredients"][0]["missingAmount"] == 100
    assert state.meals[0]["servings"] == 4
    assert state.guests[0]["title"] == "Tiramisu"
    assert state.meals[0]["ingredients"][0]["quantity"] == "200 g"
    restored = DemoState(config_path=path)
    assert restored.meals == state.meals
    assert restored.groceries == state.groceries
    assert restored.removeRequest(restored.meals[0]["requestId"])
    assert restored.meals == []
    assert restored.groceries == state.groceries
    assert DemoState(config_path=path).meals == []


def test_failed_save_keeps_recipes_pantry_and_purchases_unchanged(
    qt_app, tmp_path, monkeypatch, fake_recipes
):
    state = DemoState(config_path=tmp_path / "config.toml")
    result = result_for(state, fake_recipes)
    before = state.planning_context()

    def fail(*args):
        raise PermissionError("read only")

    monkeypatch.setattr("meal_planner_ai.storage.coordinator.os.replace", fail)
    with pytest.raises(OSError):
        state.apply_execution(result)
    assert state.planning_context() == before
    assert state.meals == state.groceries == []


def test_old_meal_records_still_load_without_recipe(qt_app, tmp_path):
    path = tmp_path / "data" / "coordinator.json"
    path.parent.mkdir()
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "meals": [
                    {
                        "id": "old",
                        "title": "Tiramisu",
                        "servings": 2,
                        "period": {"start": "2026-10-05", "end": "2026-10-11"},
                    }
                ],
                "groceries": [],
            }
        )
    )
    state = DemoState(config_path=tmp_path / "config.toml")
    assert not state.coordinatorError
    assert state.requestedMeals[0]["id"] == "old"
    assert state.meals == []


def test_direct_purchase_and_clarification_skip_recipe_model(qt_app):
    state = DemoState()

    def unexpected(payload):
        pytest.fail("No recipe generation for a purchase or clarification")

    for proposal in (
        CoordinatorProposal(clarification="Combien de pommes ?"),
        CoordinatorProposal(
            actions=[
                {
                    "service": "grocery_add",
                    "name": "Rice",
                    "amount": 100,
                    "unit": "g",
                    "category": "Épicerie",
                }
            ]
        ),
    ):
        graph = build_meal_workflow(
            coordinator_reason=lambda state: {"proposal": proposal},
            recipe_reason=unexpected,
        )
        result = graph.invoke({"request": "test", "context": state.planning_context()})[
            "result"
        ]
        assert result.meals == []
        if result.commands.clarification:
            assert result.groceries == []
        else:
            state.apply_execution(result)
            assert state.groceries[0]["name"] == "Riz"


def test_progress_and_auto_save_use_two_structured_glm_calls(
    qt_app, tmp_path, monkeypatch, fake_recipes
):
    state = DemoState(config_path=tmp_path / "config.toml")
    state.setGlmApiKey("test-secret")
    calls = []
    ready, release = Event(), Event()

    @contextmanager
    def respond(request, timeout):
        payload = json.loads(request.data)
        calls.append(payload)
        assert request.get_header("Authorization") == "Bearer test-secret"
        assert "test-secret" not in request.data.decode()
        assert payload["response_format"] == {"type": "json_object"}
        if len(calls) == 1:
            ready.set()
            assert release.wait(3)
            body = {"actions": [meal_action()]}
        else:
            data = json.loads(payload["messages"][1]["content"])
            body = json.loads(fake_recipes("", data, "test-secret"))
        yield io.StringIO(
            json.dumps(
                {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {"content": json.dumps(body)},
                        }
                    ]
                }
            )
        )

    # Exercise the actual recipe provider, replacing only HTTP transport.
    from meal_planner_ai.providers.glm import complete_json

    monkeypatch.setattr(
        "meal_planner_ai.agents.meal_planning.agent.complete_json", complete_json
    )
    monkeypatch.setattr("meal_planner_ai.providers.glm.urlopen", respond)
    assistant = state.assistant
    try:
        assistant.plan("J’ai envie de faire un tiramisu cette semaine")
        assert ready.wait(2)
        QTest.qWait(20)
        assert assistant.busy
        assert "attente" in assistant.status
        assert len(assistant.steps) == 1
        assert state.meals == []
        release.set()
        wait_for_job(assistant)
        assert not assistant.error
        assert len(calls) == 2
        assert "this_week" in calls[0]["messages"][0]["content"]
        assert "schema" in calls[1]["messages"][0]["content"]
        assert state.meals[0]["title"] == "Tiramisu"
        assert state.meals[0]["servings"] == 2
        assert assistant.proposal == {}
        assert assistant.completedActions[0].startswith("Repas ajouté : Tiramisu")
        assert assistant.steps[-1].startswith("Terminé")
        assert "enregistrée" in assistant.reply
        assert DemoState(config_path=tmp_path / "config.toml").meals == state.meals
        state.setLanguage("en")
        assert assistant.status.startswith("Done")
        assert assistant.steps[0].startswith("GLM: sending")
    finally:
        release.set()
        assistant.shutdown()


def test_recipe_provider_failure_after_interpretation_is_visible(qt_app, monkeypatch):
    state = DemoState()
    state.setGlmApiKey("key")
    monkeypatch.setattr(
        "meal_planner_ai.workflow.coordinator.interpret_request",
        lambda state, key: {"proposal": {"actions": [meal_action()]}},
    )

    def unavailable(*args):
        raise CoordinatorUnavailable("GLM indisponible. Vérifiez votre connexion.")

    monkeypatch.setattr(
        "meal_planner_ai.agents.meal_planning.agent.complete_json", unavailable
    )
    state.assistant.plan("Tiramisu")
    wait_for_job(state.assistant)
    assert "GLM indisponible" in state.assistant.error
    assert "Aucun changement" in state.assistant.status
    assert state.meals == state.groceries == []
    state.assistant.shutdown()


@pytest.mark.parametrize(
    "today,start,end",
    [
        ("2026-10-07", "2026-10-05", "2026-10-11"),
        ("2026-10-11", "2026-10-05", "2026-10-11"),
        ("2027-01-01", "2026-12-28", "2027-01-03"),
    ],
)
def test_this_week_is_a_calendar_week(today, start, end):
    assert resolve_period("this_week", {"today": today}) == Period(start=start, end=end)


def test_manual_servings_scale_recipe_and_persist(qt_app, tmp_path, fake_recipes):
    path = tmp_path / "config.toml"
    state = DemoState(config_path=path)
    state.apply_execution(result_for(state, fake_recipes))
    state.setGuests(0, 1)
    assert state.addIngredientToGroceries(0, 0)
    purchases = state.groceries
    assert state.setMealServings(0, 6)
    assert state.settings["people"] == 2
    assert state.meals[0]["baseServings"] == 6
    assert state.meals[0]["servings"] == 7
    assert state.meals[0]["ingredients"][0]["quantity"] == "350 g"
    assert state.meals[0]["ingredients"][0]["missingAmount"] == 200
    assert state.groceries == purchases
    restored = DemoState(config_path=path)
    assert restored.meals == state.meals
    assert restored.groceries == purchases
    assert state.setMealServings(0, 2)
    assert state.meals[0]["ingredients"][0]["quantity"] == "150 g"
    before = state.meals
    for index, servings in [(-1, 6), (1, 6), (0, 0), (0, 33)]:
        assert not state.setMealServings(index, servings)
        assert state.meals == before


def test_servings_save_failure_preserves_meal(qt_app, monkeypatch, fake_recipes):
    state = DemoState()
    state.apply_execution(result_for(state, fake_recipes))
    before = state.meals

    def fail(data):
        raise OSError("cannot save")

    monkeypatch.setattr(state, "_save_coordinator", fail)
    assert not state.setMealServings(0, 6)
    assert state.meals == before


def test_recipe_servings_control_updates_quantities(qt_app, fake_recipes):
    from pathlib import Path

    from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject
    from PySide6.QtQml import QQmlApplicationEngine

    from meal_planner_ai.ui import app

    state = DemoState()
    state.apply_execution(result_for(state, fake_recipes))
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(str(e) for e in errors))
    engine.setInitialProperties({"demo": state})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    assert engine.rootObjects(), warnings
    window = engine.rootObjects()[0]
    try:
        assert window.property("pageTitles").toVariant()[0] == "Mes repas"
        dialog = window.findChild(QObject, "recipeDialog")
        dialog.setProperty("mealId", 0)
        QMetaObject.invokeMethod(dialog, "open")
        QTest.qWait(20)
        picker = dialog.findChild(QObject, "mealServingsPicker")
        assert picker.property("value") == 2
        picker.setProperty("value", 6)
        assert QMetaObject.invokeMethod(picker, "valueModified")
        qt_app.processEvents()
        assert state.meals[0]["ingredients"][0]["quantity"] == "300 g"
        assert state.meals[0]["servings"] == 6
        assert state.groceries == []
        assert not warnings, "\n".join(warnings)
    finally:
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
