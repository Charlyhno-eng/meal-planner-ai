"""Coordinator routing, atomic services, provider boundaries and desktop integration."""

import io
import json
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError

import pytest
from pydantic import ValidationError
from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest

from meal_planner_ai.agents.coordinator import (
    GLM_MODEL,
    GLM_URL,
    CoordinatorUnavailable,
    interpret_request,
)
from meal_planner_ai.models.coordinator import CoordinatorProposal, Period
from meal_planner_ai.ui import app
from meal_planner_ai.ui.demo import DemoState
from meal_planner_ai.workflow.coordinator import (
    build_coordinator_workflow,
    resolve_period,
)


def actions():
    return [
        {"service": "meal_request", "title": "Tiramisu", "servings": 6},
        {
            "service": "grocery_add",
            "name": "Potatoes",
            "amount": 3,
            "unit": "pièce",
            "category": "Fruits & légumes",
            "period": "next_week",
        },
        {
            "service": "pantry_set",
            "name": "Rice",
            "amount": 500,
            "unit": "g",
            "category": "Épicerie",
        },
    ]


def routed(state, raw=None):
    workflow = build_coordinator_workflow(
        reason=lambda s: {"proposal": raw or {"actions": actions()}}
    )
    context = state.planning_context()
    context["today"] = "2026-10-07"
    return workflow.invoke({"request": "tiramisu and groceries", "context": context})


def wait_for_job(assistant):
    for _ in range(100):
        QTest.qWait(10)
        if not assistant.busy:
            return
    pytest.fail("Coordinator job did not finish")


def test_routes_without_recipes_and_applies_only_requested_services(qt_app, tmp_path):
    state = DemoState(config_path=tmp_path / "config.toml")
    assert state.recipe_catalogue == []
    before = state.planning_context()
    result = routed(state)
    assert state.planning_context() == before
    assert [item["service"] for item in result["routed"]] == [
        "meal_request",
        "grocery_add",
        "pantry_set",
    ]
    assert result["routed"][1]["period"] == {"start": "2026-10-12", "end": "2026-10-18"}
    state.apply_commands(result["proposal"])
    assert state.settings == before["settings"]
    assert state.meals == []  # A coordinator does not invent a recipe.
    assert state.requestedMeals[0]["title"] == "Tiramisu"
    assert state.requestedMeals[0]["servings"] == 6
    assert state.groceries[0]["name"] == "Pommes de terre"
    assert state.groceries[0]["quantity"] == "3 pièces"
    assert state.groceries[0]["periodLabel"] == "2026-10-12 — 2026-10-18"
    assert state.pantry[0]["name"] == "Riz"
    assert state.pantry[0]["amount"] == 500
    # Applying twice appends explicit purchases; inventory is an absolute update.
    state.apply_commands(result["proposal"])
    assert len(state.pantry) == 1
    assert len(state.groceries) == 2
    assert len(state.requestedMeals) == 2
    restored = DemoState(config_path=tmp_path / "config.toml")
    assert restored.requestedMeals == state.requestedMeals
    assert restored.groceries == state.groceries
    assert state.removeRequest(state.requestedMeals[0]["id"])
    assert state.removeRequest(state.groceries[0]["requestId"])
    restored = DemoState(config_path=tmp_path / "config.toml")
    assert len(restored.requestedMeals) == len(restored.groceries) == 1
    state.setLanguage("en")
    state.toggleGrocery(state.groceries[0]["id"])
    state.copyGroceries()
    assert (
        "✓ Potatoes — 3 pieces (2026-10-12 — 2026-10-18)" in qt_app.clipboard().text()
    )


@pytest.mark.parametrize(
    "change",
    [
        {"amount": -3},
        {"amount": 0},
        {"amount": "3"},
        {"amount": True},
        {"amount": float("inf")},
        {"amount": float("nan")},
        {"amount": 1.5},
        {"unit": "kg"},
        {"name": "  "},
        {"category": "unsupported"},
        {"period": {"start": "2026-10-18", "end": "2026-10-12"}},
        {"period": {"start": 0, "end": 10000}},
        {"unexpected": "data"},
    ],
)
def test_invalid_action_rejects_the_whole_batch(qt_app, change):
    state = DemoState()
    before = state.planning_context()
    raw = actions()
    raw[1].update(change)
    with pytest.raises(ValidationError):
        routed(state, {"actions": raw})
    assert state.planning_context() == before
    assert state.groceries == state.requestedMeals == state.pantry == []


@pytest.mark.parametrize("servings", [0, 33, True, "6", 6.5])
def test_strict_servings(servings):
    with pytest.raises(ValidationError):
        CoordinatorProposal(
            actions=[
                {"service": "meal_request", "title": "Tiramisu", "servings": servings}
            ]
        )


def test_unsupported_service_and_empty_response_are_rejected():
    for raw in (
        {"actions": []},
        {"actions": [{"service": "shell"}]},
        {"actions": actions(), "clarification": "Which meal?"},
    ):
        with pytest.raises(ValidationError):
            CoordinatorProposal.model_validate(raw)


@pytest.mark.parametrize(
    "today,start,end",
    [
        ("2026-10-12", "2026-10-19", "2026-10-25"),
        ("2026-10-18", "2026-10-19", "2026-10-25"),
        ("2026-12-31", "2027-01-04", "2027-01-10"),
    ],
)
def test_next_week_is_resolved_deterministically(today, start, end):
    period = resolve_period("next_week", {"today": today})
    assert period == Period(start=start, end=end)
    assert period.start.weekday() == 0 and period.end.weekday() == 6


@pytest.mark.parametrize("excluded", ["potatoes", "pommes de terre", "POTATOES"])
def test_exclusions_reject_purchase_before_any_service_mutation(qt_app, excluded):
    state = DemoState()
    state.configure("2026-10-07", 7, 7, 2, False, excluded)
    before = state.planning_context()
    with pytest.raises(ValueError, match="excluded food"):
        routed(state)
    assert state.planning_context() == before


def test_failed_persistence_keeps_all_services_unchanged(qt_app, tmp_path, monkeypatch):
    state = DemoState(config_path=tmp_path / "config.toml")
    commands = routed(state)["proposal"]
    before = state.planning_context()

    def fail(*args):
        raise PermissionError("read only")

    monkeypatch.setattr("meal_planner_ai.storage.coordinator.os.replace", fail)
    with pytest.raises(OSError):
        state.apply_commands(commands)
    assert state.planning_context() == before
    assert list((tmp_path / "data").iterdir()) == []
    assert state._next_id == 1


def test_corrupt_persistence_is_visible_and_never_overwritten(qt_app, tmp_path):
    path = tmp_path / "data" / "coordinator.json"
    path.parent.mkdir()
    path.write_text('{"version":99}')
    state = DemoState(config_path=tmp_path / "config.toml")
    assert state.coordinatorError
    with pytest.raises(ValueError):
        state.apply_commands(routed(state)["proposal"])
    assert path.read_text() == '{"version":99}'
    assert not state.removeRequest("missing")


def test_glm_uses_structured_json_and_keeps_credentials_out_of_context(monkeypatch):
    calls = []

    @contextmanager
    def respond(request, timeout):
        calls.append(request)
        assert request.full_url == GLM_URL
        assert request.get_header("Authorization") == "Bearer secret-key"
        assert timeout == 120
        payload = json.loads(request.data)
        assert payload["model"] == GLM_MODEL
        assert payload["response_format"] == {"type": "json_object"}
        assert "secret-key" not in request.data.decode()
        assert "meal_request" in payload["messages"][0]["content"]
        assert "next_week" in payload["messages"][0]["content"]
        yield io.StringIO(
            json.dumps(
                {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {"content": json.dumps({"actions": actions()})},
                        }
                    ]
                }
            )
        )

    monkeypatch.setattr("meal_planner_ai.providers.glm.urlopen", respond)
    result = interpret_request({"request": "a tiramisu", "context": {}}, "secret-key")
    assert len(result["proposal"].actions) == 3
    assert len(calls) == 1


@pytest.mark.parametrize("code", [401, 403, 429, 500])
def test_provider_errors_do_not_expose_credentials_or_response_body(monkeypatch, code):
    def fail(*args, **kwargs):
        raise HTTPError(GLM_URL, code, "secret-key", {}, io.BytesIO(b"secret-key"))

    monkeypatch.setattr("meal_planner_ai.providers.glm.urlopen", fail)
    with pytest.raises(CoordinatorUnavailable) as error:
        interpret_request({"request": "test", "context": {}}, "secret-key")
    assert "secret-key" not in str(error.value)


@pytest.mark.parametrize(
    "body",
    [
        "not json",
        '{"choices":[]}',
        json.dumps(
            {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}
        ),
        json.dumps(
            {"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]}
        ),
    ],
)
def test_invalid_or_truncated_provider_output_is_rejected(monkeypatch, body):
    @contextmanager
    def respond(*args, **kwargs):
        yield io.StringIO(body)

    monkeypatch.setattr("meal_planner_ai.providers.glm.urlopen", respond)
    with pytest.raises(ValueError):
        interpret_request({"request": "test", "context": {}}, "key")


def test_clarification_follow_up_and_stale_context(qt_app, monkeypatch, fake_recipes):
    state = DemoState()
    state.setGlmApiKey("key")
    calls = []

    def reason(s, key):
        calls.append(s)
        if len(calls) == 1:
            return {
                "proposal": CoordinatorProposal(clarification="Combien de pommes ?")
            }
        assert s["conversation"][-1]["content"] == "Combien de pommes ?"
        return {"proposal": CoordinatorProposal(actions=[actions()[0]])}

    monkeypatch.setattr(
        "meal_planner_ai.workflow.coordinator.interpret_request", reason
    )
    from threading import Event

    ready, release = Event(), Event()

    def blocked_recipe(system, payload, api_key):
        ready.set()
        assert release.wait(2)
        return fake_recipes(system, payload, api_key)

    monkeypatch.setattr(
        "meal_planner_ai.agents.meal_planning.agent.complete_json", blocked_recipe
    )
    assistant = state.assistant
    try:
        assistant.plan("Ajouter des pommes")
        wait_for_job(assistant)
        assert assistant.reply == "Combien de pommes ?"
        assert assistant.proposal == {}
        assistant.plan("Trois, et un tiramisu pour six")
        assert ready.wait(2)
        state.saveFood(-1, "Rice", 100, "g", "Épicerie")
        release.set()
        wait_for_job(assistant)
        assert "changé" in assistant.error
        assert state.requestedMeals == []
        assert assistant.proposal == {}
        assert state.meals == []
        assert "Aucun changement" in assistant.status
    finally:
        release.set()
        assistant.shutdown()


def test_home_voice_text_purchase_and_planned_meal_views(
    qt_app, monkeypatch, tmp_path, fake_recipes
):
    state = DemoState(config_path=tmp_path / "config.toml")
    state.setGlmApiKey("key")
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(map(str, errors)))
    engine.setInitialProperties({"demo": state})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    window = engine.rootObjects()[0]
    monkeypatch.setattr(
        "meal_planner_ai.workflow.coordinator.interpret_request",
        lambda s, key: {"proposal": CoordinatorProposal(actions=actions()[:2])},
    )
    try:
        from test_bootstrap import visual_child

        request = visual_child(window.contentItem(), "planningRequest")
        # Local transcription enters the very same input used by typed requests.
        state.assistant._transcribed("Un tiramisu pour six personnes", "")
        assert request.property("text") == "Un tiramisu pour six personnes"
        request.setProperty(
            "text",
            request.property("text")
            + ". Trois pommes de terre à acheter la semaine prochaine",
        )
        button = visual_child(window.contentItem(), "generatePlanButton")
        QMetaObject.invokeMethod(button, "click")
        wait_for_job(state.assistant)
        assert state.assistant.proposal == {}
        assert len(state.assistant.completedActions) == 2
        assert state.requestedMeals == []
        assert state.meals[0]["title"] == "Tiramisu"
        assert state.meals[0]["servings"] == 6
        assert (
            next(item for item in state.groceries if item.get("requestId"))["quantity"]
            == "3 pièces"
        )
        assert "enregistrée" in state.assistant.reply
        for language in ("fr", "en"):
            state.setLanguage(language)
            for index in (0, 2, 5):
                window.setProperty("currentPage", index)
                QTest.qWait(20)
        assert (
            next(item for item in state.groceries if item.get("requestId"))["name"]
            == "Potatoes"
        )
        assert not warnings, "\n".join(warnings)
    finally:
        state.assistant.shutdown()
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


def test_existing_purchase_checks_survive_new_commands(qt_app):
    state = DemoState()
    state.apply_commands(routed(state)["proposal"])
    key = state.groceries[0]["id"]
    state.toggleGrocery(key)
    state.apply_commands(routed(state)["proposal"])
    assert next(item for item in state.groceries if item["id"] == key)["checked"]


def test_no_key_no_network_and_malformed_response_no_application(qt_app, monkeypatch):
    state = DemoState()
    called = []

    def unexpected(*args, **kwargs):
        called.append(True)
        raise ValueError("secret-provider-body")

    monkeypatch.setattr("meal_planner_ai.providers.glm.urlopen", unexpected)
    assistant = state.assistant
    try:
        assistant.plan("Un tiramisu pour six")
        assert not called
        assert not assistant.busy
        assert "GLM" in assistant.error
        state.setGlmApiKey("key")
        assistant.plan("Un tiramisu pour six")
        wait_for_job(assistant)
        assert called == [True]
        assert assistant.proposal == {}
        assert "secret-provider-body" not in assistant.error
        assert state.requestedMeals == state.groceries == []
    finally:
        assistant.shutdown()
