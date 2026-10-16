"""Intolerance checks cover recipes, computed needs, and explicit purchases."""

import pytest

from src.agents.intolerance_verification import (
    IntoleranceConflict,
    check_intolerances,
)
from src.models.coordinator import GroceryAdd, RequestedMeal
from src.models.groceries import GroceryRequirement
from src.models.recipes import Ingredient, Recipe
from src.ui.demo import DemoState
from src.workflow.meal_request import build_meal_workflow


def settings(intolerance):
    return {
        "members": [
            {"name": "Alice", "intolerances": ""},
            {"name": "Bob", "intolerances": intolerance},
        ]
    }


@pytest.mark.parametrize(
    "intolerance,food",
    [
        ("LACTOSE", "Mascarpone"),
        ("gluten", "Bread"),
        ("eggs", "Œufs"),
        ("saumon", "Salmon"),
    ],
)
@pytest.mark.parametrize("source", ["recipe", "requirement", "purchase"])
def test_rejects_each_members_conflicts(intolerance, food, source):
    ingredient = Ingredient(name=food, amount=100, unit="g", category="Épicerie")
    meals, groceries = [], []
    if source == "recipe":
        meals.append(
            RequestedMeal(
                title="Test",
                servings=2,
                period={"start": "2026-10-16", "end": "2026-10-16"},
                recipe=Recipe(
                    title="Test",
                    servings=2,
                    subtitle="Test",
                    minutes=10,
                    vegetarian=True,
                    ingredients=[ingredient],
                    steps=["Prepare."],
                ),
            )
        )
    elif source == "requirement":
        # A fully stocked ingredient must still be checked.
        groceries.append(
            GroceryRequirement(
                **ingredient.model_dump(exclude={"amount"}),
                required=100,
                available=100,
                amount=0,
            )
        )
    else:
        groceries.append(GroceryAdd(service="grocery_add", **ingredient.model_dump()))
    with pytest.raises(IntoleranceConflict):
        check_intolerances(meals, groceries, settings(intolerance))


def test_compatible_food_and_empty_intolerances_pass():
    rice = Ingredient(name="Rice", amount=100, unit="g", category="Épicerie")
    check_intolerances([], [rice], settings("gluten, lactose"))
    check_intolerances([], [rice], {})


def test_graph_verifies_existing_recipe_needs_on_purchase_only_path(qt_app):
    state = DemoState()
    context = state.planning_context()
    context["settings"].update(settings("gluten"))
    context["planned_ingredients"] = [
        Ingredient(name="Bread", amount=100, unit="g", category="Épicerie").model_dump()
    ]
    graph = build_meal_workflow(
        coordinator_reason=lambda _: {
            "proposal": {
                "actions": [
                    {
                        "service": "grocery_add",
                        "name": "Rice",
                        "amount": 100,
                        "unit": "g",
                        "category": "Épicerie",
                    }
                ]
            }
        }
    )
    before = state.planning_context()
    with pytest.raises(IntoleranceConflict):
        graph.invoke({"request": "Buy rice", "context": context})
    assert state.planning_context() == before
    assert "intolerance_verification" in graph.get_graph().nodes


def test_save_rechecks_current_intolerances_before_any_mutation(
    qt_app, tmp_path, fake_recipes
):
    from test_meal_workflow import result_for

    state = DemoState(config_path=tmp_path / "config.toml")
    state.apply_execution(result_for(state, fake_recipes))
    result = result_for(
        state,
        fake_recipes,
        actions=[
            {
                "service": "grocery_add",
                "name": "Rice",
                "amount": 100,
                "unit": "g",
                "category": "Épicerie",
            }
        ],
    )
    # Simulate a household change after the workflow snapshot was taken.
    state._settings.update(settings("lactose"))
    before = state.planning_context()
    saved = (tmp_path / "data" / "coordinator.json").read_bytes()
    with pytest.raises(IntoleranceConflict):
        state.apply_execution(result)
    assert state.planning_context() == before
    assert (tmp_path / "data" / "coordinator.json").read_bytes() == saved


def test_shared_exclusions_keep_intolerance_source_checks():
    milk = Ingredient(name="Milk", amount=100, unit="ml", category="Épicerie")
    with pytest.raises(IntoleranceConflict):
        check_intolerances([], [milk], {"dislikes": "lactose", "members": []})
