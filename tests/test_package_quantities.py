"""Unknown package weights must be resolved before stock can cover a recipe."""

import json

import pytest

from src.agents.coordinator.agent import interpret_request
from src.ui.demo import DemoState
from src.workflow.meal_request import build_meal_workflow


def plan(state, fake_recipes, corrections=()):
    def recipes(payload):
        batch = json.loads(fake_recipes("", payload, "key"))
        batch["recipes"][0]["ingredients"][0]["amount"] = 500
        return batch

    return build_meal_workflow(
        coordinator_reason=lambda s: {
            "proposal": {
                "actions": [
                    {"service": "meal_request", "title": "Tiramisu", "servings": 2},
                    *corrections,
                ]
            }
        },
        recipe_reason=recipes,
    ).invoke({"request": "Tiramisu", "context": state.planning_context()})["result"]


def stock(amount, unit):
    return {
        "service": "pantry_set",
        "name": "Mascarpone",
        "amount": amount,
        "unit": unit,
        "category": "Produits frais",
    }


@pytest.mark.parametrize("language", ["fr", "en"])
def test_unknown_package_size_asks_before_applying(qt_app, fake_recipes, language):
    state = DemoState()
    state.setLanguage(language)
    state.saveFood(-1, "Mascarpone", 2, "pièce", "Produits frais")
    before = state.planning_context()
    result = plan(state, fake_recipes)
    question = result.commands.clarification
    assert "Mascarpone (500 g)" in question
    assert (
        "weight or volume" if language == "en" else "poids ou le volume"
    ) in question
    assert result.meals == result.groceries == []
    assert state.planning_context() == before
    with pytest.raises(ValueError, match="clarification"):
        state.apply_execution(result)


@pytest.mark.parametrize("total,missing", [(500, 0), (400, 100)])
def test_confirmed_total_replaces_packages_and_covers_recipe(
    qt_app, tmp_path, fake_recipes, total, missing
):
    path = tmp_path / "config.toml"
    state = DemoState(config_path=path)
    state.saveFood(-1, "Mascarpone", 2, "pièce", "Produits frais")
    result = plan(state, fake_recipes, [stock(0, "pièce"), stock(total, "g")])
    assert not result.commands.clarification
    need = next(item for item in result.groceries if item.name == "Mascarpone")
    assert need.available == total
    assert need.amount == missing
    state.apply_execution(result)
    assert len(state.meals) == 1
    assert state.meals[0]["ingredients"][0]["missingAmount"] == missing
    assert state.pantry[0]["amount"] == 0
    assert state.pantry[1]["amount"] == total


def test_new_ambiguous_stock_in_same_request_is_detected(qt_app, fake_recipes):
    state = DemoState()
    result = plan(state, fake_recipes, [stock(2, "pièce")])
    assert result.commands.clarification
    assert state.pantry == state.meals == []


def test_sufficient_measured_stock_needs_no_package_clarification(qt_app, fake_recipes):
    state = DemoState()
    state.saveFood(-1, "Mascarpone", 2, "pièce", "Produits frais")
    state.saveFood(-1, "Mascarpone", 500, "g", "Produits frais")
    result = plan(state, fake_recipes)
    assert not result.commands.clarification
    assert result.groceries[0].amount == 0


def test_coordinator_gets_package_and_follow_up_rules(monkeypatch):
    calls = []

    def respond(system, payload, key):
        calls.append((system, payload))
        return json.dumps({"clarification": "Quel poids par pot ?"})

    monkeypatch.setattr("src.agents.coordinator.agent.complete_json", respond)
    interpret_request({"request": "J'ai deux mascarpones", "context": {}}, "key")
    system = calls[0][0]
    assert "never guess a package weight or volume" in system
    assert "two 250 g tubs -> 500 g total" in system
    assert "preserve the original" in system
    assert "pantry_set amount 0 unit pièce" in system


def test_assistant_keeps_original_request_for_package_size_follow_up(
    qt_app, monkeypatch, fake_recipes
):
    from test_meal_workflow import wait_for_job

    state = DemoState()
    state.setGlmApiKey("key")
    state.saveFood(-1, "Mascarpone", 2, "pièce", "Produits frais")
    calls = []

    def interpret(snapshot, key):
        calls.append(snapshot)
        corrections = []
        if len(calls) == 2:
            assert snapshot["request"] == "250 g par pot"
            assert snapshot["conversation"][0]["content"] == "Un tiramisu"
            assert "500 g" in snapshot["conversation"][1]["content"]
            corrections = [stock(0, "pièce"), stock(500, "g")]
        return {
            "proposal": {
                "actions": [
                    {"service": "meal_request", "title": "Tiramisu", "servings": 2},
                    *corrections,
                ]
            }
        }

    def recipes(system, payload, key):
        batch = json.loads(fake_recipes(system, payload, key))
        batch["recipes"][0]["ingredients"][0]["amount"] = 500
        return json.dumps(batch)

    monkeypatch.setattr("src.workflow.coordinator.interpret_request", interpret)
    monkeypatch.setattr("src.agents.meal_planning.agent.complete_json", recipes)
    assistant = state.assistant
    try:
        assistant.plan("Un tiramisu")
        wait_for_job(assistant)
        assert not assistant.error
        assert "500 g" in assistant.reply
        assert state.meals == []
        assert state.pantry[0]["amount"] == 2
        assistant.plan("250 g par pot")
        wait_for_job(assistant)
        assert not assistant.error
        assert len(state.meals) == 1
        assert state.meals[0]["ingredients"][0]["missingAmount"] == 0
        assert state.pantry[0]["amount"] == 0
        assert state.pantry[1]["amount"] == 500
    finally:
        assistant.shutdown()
