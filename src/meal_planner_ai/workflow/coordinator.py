"""LangGraph extraction, validation and routing, without session mutations."""

from datetime import date, timedelta
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from meal_planner_ai.agents.coordinator import interpret_request
from meal_planner_ai.models.coordinator import (
    CoordinatorProposal,
    Period,
)
from meal_planner_ai.ui.i18n import ENGLISH, canonical_food


class CoordinatorState(TypedDict, total=False):
    request: str
    context: dict
    conversation: list[dict]
    proposal: CoordinatorProposal
    index: int
    routed: list[dict]


def resolve_period(period, context: dict) -> Period:
    if isinstance(period, Period):
        return period
    if period in ("this_week", "next_week"):
        today = date.fromisoformat(context["today"])
        offset = 7 if period == "next_week" else 0
        start = today + timedelta(days=offset - today.weekday())
        return Period(start=start, end=start + timedelta(days=6))
    settings = context["settings"]
    start = date.fromisoformat(settings["start"])
    return Period(start=start, end=start + timedelta(days=settings["days"] - 1))


def build_coordinator_workflow(api_key: str = "", reason=None):
    def extract(state):
        return (reason or (lambda s: interpret_request(s, api_key)))(state)

    def validate(state):
        # Revalidate even model instances constructed by a custom reasoner.
        raw = state["proposal"]
        proposal = CoordinatorProposal.model_validate(
            raw.model_dump() if isinstance(raw, CoordinatorProposal) else raw
        )
        actions = []
        excluded = [
            word.strip().casefold()
            for word in state["context"]["settings"]["dislikes"].split(",")
            if word.strip()
        ]
        for action in proposal.actions:
            values = action.model_dump()
            if action.service != "pantry_set":
                values["period"] = resolve_period(action.period, state["context"])
            if action.service != "meal_request":
                values["name"] = canonical_food(action.name)
            if action.service == "grocery_add" and any(
                word in action.name.casefold()
                or word in canonical_food(action.name).casefold()
                or word in ENGLISH.get(values["name"], values["name"]).casefold()
                for word in excluded
            ):
                raise ValueError("Purchase contains an excluded food")
            actions.append(values)
        return {
            "proposal": CoordinatorProposal(actions=actions) if actions else proposal,
            "index": 0,
            "routed": [],
        }

    def route(state):
        actions = state["proposal"].actions
        return actions[state["index"]].service if state["index"] < len(actions) else END

    def dispatch(state):
        # Each node stages its service command; applying remains one atomic operation.
        action = state["proposal"].actions[state["index"]]
        return {
            "routed": [*state["routed"], action.model_dump(mode="json")],
            "index": state["index"] + 1,
        }

    graph = StateGraph(CoordinatorState)
    graph.add_node("interpret", extract)
    graph.add_node("validate", validate)
    graph.add_edge(START, "interpret")
    graph.add_edge("interpret", "validate")
    routes = {name: name for name in ("meal_request", "grocery_add", "pantry_set")}
    routes[END] = END
    graph.add_conditional_edges("validate", route, routes)
    for service in ("meal_request", "grocery_add", "pantry_set"):
        graph.add_node(service, dispatch)
        graph.add_conditional_edges(service, route, routes)
    return graph.compile()
