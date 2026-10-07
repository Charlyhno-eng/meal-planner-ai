"""Local LLM reasoning followed by deterministic proposal validation."""

import json
import os
from typing import TypedDict
from urllib.error import URLError
from urllib.request import Request, urlopen

from langgraph.graph import END, START, StateGraph

from meal_planner_ai.models.planning import PlanningProposal, validate_recipes


class PlanningState(TypedDict, total=False):
    request: str
    context: dict
    proposal: PlanningProposal


def ask_local_model(state: PlanningState) -> dict:
    model = os.environ.get("MEAL_PLANNER_OLLAMA_MODEL", "qwen3:8b")
    system = (
        "Plan meals using ONLY the supplied recipe catalogue. Return the JSON schema. "
        "Interpret the user's request in French or English. Keep current settings and "
        "guests unless asked to change them. Use existing pantry quantities to reduce "
        "purchases. Pantry updates are absolute available quantities, only for foods "
        "explicitly declared by the user; never invent quantities. "
        "Use French canonical "
        "ingredient names and units. Meals are an ordered list for the whole period, "
        "without assigned days or lunch/dinner slots. Meal count is independent of "
        "period length. Meal indices are zero-based in recipe_ids order. "
        "Account for guests by meal. Respect vegetarian diet and all excluded "
        "ingredients. Keep exclusions unless explicitly changed. Do not invent recipes."
    )
    payload = {
        "model": model,
        "stream": False,
        "format": PlanningProposal.model_json_schema(),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(state, ensure_ascii=False)},
        ],
        "options": {"temperature": 0},
    }
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            result = json.load(response)
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(
            "Ollama indisponible. Démarrez Ollama avec un modèle local déjà installé "
            "(MEAL_PLANNER_OLLAMA_MODEL)."
        ) from exc
    return {
        "proposal": PlanningProposal.model_validate_json(result["message"]["content"])
    }


def build_planning_workflow(recipes: list[dict], english: dict, reason=ask_local_model):
    def verify(state: PlanningState):
        validate_recipes(state["proposal"], recipes, english)
        return {}

    graph = StateGraph(PlanningState)
    graph.add_node("meal_planning", reason)
    graph.add_node("preference_verification", verify)
    graph.add_edge(START, "meal_planning")
    graph.add_edge("meal_planning", "preference_verification")
    graph.add_edge("preference_verification", END)
    return graph.compile()
