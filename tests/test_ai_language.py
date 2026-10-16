"""The interface language overrides input language for both AI agents."""

import json

import pytest

from src.agents.coordinator.agent import interpret_request
from src.agents.meal_planning.agent import plan_meals
from src.models.coordinator import CoordinatorProposal, MealRequest
from src.ui.demo import DemoState


@pytest.mark.parametrize("language,name", [("en", "English"), ("fr", "French")])
def test_both_agents_receive_explicit_language_policy(
    qt_app, monkeypatch, fake_recipes, language, name
):
    store = DemoState()
    store.setLanguage(language)
    context = store.planning_context()
    calls = []

    def coordinator(system, payload, key):
        calls.append(system)
        assert payload["context"]["language"] == language
        return json.dumps({"clarification": "How many servings?"})

    def recipes(system, payload, key):
        calls.append(system)
        assert payload["language"] == language
        assert [meal["title"] for meal in payload["meals"]] == [
            "Tiramisu",
            "Lasagnes aux légumes",
        ]
        response = json.loads(fake_recipes(system, payload, key))
        if language == "en":
            response["recipes"][1]["title"] = "Vegetable lasagne"
        return response

    monkeypatch.setattr("src.agents.coordinator.agent.complete_json", coordinator)
    monkeypatch.setattr("src.agents.meal_planning.agent.complete_json", recipes)
    interpret_request({"request": "Je veux des lasagnes", "context": context}, "key")
    meals = plan_meals(
        [
            MealRequest(
                service="meal_request",
                title=title,
                servings=2,
                period={"start": "2026-10-16", "end": "2026-10-22"},
            )
            for title in ("Tiramisu", "Lasagnes aux légumes")
        ],
        context,
        "key",
    )
    assert meals[1].title == (
        "Vegetable lasagne" if language == "en" else "Lasagnes aux légumes"
    )
    for system in calls:
        assert f"The application language is {name}" in system
        assert "regardless of the language of the request" in system
        assert "review EACH recipe and clarification" in system
    assert "Keep each requested title" not in calls[1]
    assert "clarification in the user's language" not in calls[0]


@pytest.mark.parametrize("clarification", [False, True])
def test_language_switch_rejects_pending_ai_result(qt_app, clarification):
    store = DemoState()
    assistant = store.assistant
    assistant._context = store.planning_context()
    store.setLanguage("en")
    proposal = CoordinatorProposal(
        actions=[]
        if clarification
        else [MealRequest(service="meal_request", title="Lasagnes", servings=2)],
        clarification="Combien de personnes ?" if clarification else None,
    )
    assistant._planned(proposal, "")
    assert assistant.error == "The data has changed. Send your request again."
    assert assistant.reply == ""
    assert assistant.proposal == {}
    assert store.meals == []
