"""Check user-facing preview state without invoking real planning agents."""

import pytest

from meal_planner_ai.ui.demo import DemoState


def grocery(demo, name):
    return next(item for item in demo.groceries if item["name"] == name)


def test_guests_update_recipe_portions_and_purchase_shortfall():
    demo = DemoState()
    assert demo.configure("2026-10-07", 1, 1, 2, False, "")
    assert demo.meals[0]["ingredients"][2]["inPantry"]
    demo.setGuests(0, 2)
    assert demo.meals[0]["servings"] == 4
    assert demo.meals[0]["ingredients"][0]["quantity"] == "320 g"
    assert demo.meals[0]["ingredients"][2]["missingAmount"] == 1
    assert demo.groceries == []
    demo.setGuests(0, 0)
    assert demo.guests == []
    assert demo.meals[0]["ingredients"][2]["inPantry"]


def test_inventory_add_edit_remove_and_unit_matching():
    demo = DemoState()
    demo.configure("2026-10-07", 1, 1, 2, False, "")
    assert demo.saveFood(-1, "Quinoa", 80, "g", "Épicerie")
    item = demo.pantry[-1]
    assert demo.meals[0]["ingredients"][0]["missingAmount"] == 80
    assert demo.saveFood(item["id"], "Quinoa", 200, "ml", "Épicerie")
    assert demo.meals[0]["ingredients"][0]["missingAmount"] == 160
    assert demo.saveFood(item["id"], "Quinoa", 200, "g", "Épicerie")
    assert demo.meals[0]["ingredients"][0]["inPantry"]
    demo.removeFood(item["id"])
    assert demo.meals[0]["ingredients"][0]["missingAmount"] == 160
    assert not demo.saveFood(-1, "", 0, "g", "Épicerie")


def test_preferences_and_flexible_meal_list():
    demo = DemoState()
    assert demo.configure("2026-12-29", 7, 10, 3, True, "CHAMPIGNONS, pesto")
    assert len(demo.meals) == 10
    assert [meal["id"] for meal in demo.meals] == list(range(10))
    assert demo.meals[0]["label"] == "Repas 1"
    assert demo.meals[-1]["label"] == "Repas 10"
    assert all("date" not in meal and "slot" not in meal for meal in demo.meals)
    assert demo.period == "29 décembre — 4 janvier"
    assert all(meal["vegetarian"] for meal in demo.meals)
    assert not any(
        item["name"] in {"Champignons", "Pesto", "Saumon"} for item in demo.groceries
    )
    demo.replaceMeal(0)
    assert all(meal["vegetarian"] for meal in demo.meals)


@pytest.mark.parametrize(
    "start,days,count,people,excluded",
    [
        ("invalid", 7, 7, 2, ""),
        ("2026-02-30", 7, 7, 2, ""),
        ("2026-10-07", 0, 1, 2, ""),
        ("2026-10-07", 2, 29, 2, ""),
        ("9999-12-31", 2, 1, 2, ""),
        ("2026-10-07", 7, 7, 0, ""),
        (
            "2026-10-07",
            7,
            7,
            2,
            "quinoa, pâtes, lentilles, pain, saumon, riz, concombre",
        ),
    ],
)
def test_invalid_configuration_preserves_existing_state(
    start, days, count, people, excluded
):
    demo = DemoState()
    previous = demo.settings
    meals = demo.meals
    assert not demo.configure(start, days, count, people, False, excluded)
    assert demo.settings == previous
    assert demo.meals == meals


def test_checking_copy_and_replacing_a_meal(qt_app):
    demo = DemoState()
    demo.configure("2026-10-07", 1, 1, 2, False, "")
    assert demo.groceries == []
    assert demo.addIngredientToGroceries(0, 0)
    key = grocery(demo, "Quinoa")["id"]
    demo.toggleGrocery(key)
    assert grocery(demo, "Quinoa")["checked"]
    demo.copyGroceries()
    text = qt_app.clipboard().text()
    assert "✓ Quinoa — 160 g" in text
    assert "Courgettes" not in text  # Already covered by stock.
    title = demo.meals[0]["title"]
    assert demo.replaceMeal(0)
    assert demo.meals[0]["title"] != title
    assert not any(item["checked"] for item in demo.groceries)


pytestmark = pytest.mark.usefixtures("sample_session")


def test_meal_count_is_independent_of_period_and_guests_follow_meal_ids():
    demo = DemoState()
    assert demo.configure("2026-10-07", 1, 10, 2, False, "")
    assert [meal["id"] for meal in demo.meals] == list(range(10))
    demo.setGuests(8, 3)
    assert demo.guests[0]["id"] == 8
    assert demo.meals[8]["servings"] == 5
    assert demo.replaceMeal(8)
    assert demo.guests[0]["title"] == demo.meals[8]["title"]
    assert demo.meals[8]["servings"] == 5
    assert demo.configure("2026-10-07", 1, 28, 2, False, "")
    assert len(demo.meals) == 28


def test_recipe_coverage_tracks_stock_guests_and_units():
    demo = DemoState()
    demo.configure("2026-10-07", 1, 1, 2, False, "")
    courgettes = demo.meals[0]["ingredients"][2]
    assert courgettes["inPantry"]
    assert not courgettes["inGroceries"]
    demo.setGuests(0, 2)
    assert not demo.meals[0]["ingredients"][2]["inPantry"]
    assert not demo.meals[0]["ingredients"][2]["inGroceries"]
    assert demo.saveFood(-1, "Quinoa", 1000, "ml", "Épicerie")
    assert not demo.meals[0]["ingredients"][0]["inPantry"]
    assert not demo.meals[0]["ingredients"][0]["inGroceries"]
    assert demo.addIngredientToGroceries(0, 0)
    assert demo.meals[0]["ingredients"][0]["inGroceries"]


def test_uncovered_ingredient_addition_persists_and_is_idempotent(tmp_path):
    from meal_planner_ai.storage.coordinator import load_coordinator

    demo = DemoState(config_path=tmp_path / "config.toml")
    demo.configure("2026-10-07", 1, 1, 2, False, "")
    assert demo.groceries == []
    assert demo.meals[0]["ingredients"][0]["missingAmount"] == 160
    assert demo.addIngredientToGroceries(0, 0)
    assert demo.meals[0]["ingredients"][0]["inGroceries"]
    assert demo.addIngredientToGroceries(0, 0)
    data = load_coordinator(tmp_path / "data" / "coordinator.json")
    assert len(data.groceries) == 1
    assert data.groceries[0].amount == 160
    assert not demo.addIngredientToGroceries(-1, 0)
    assert not demo.addIngredientToGroceries(0, 99)


def test_uncovered_ingredient_save_failure_keeps_state(monkeypatch):
    demo = DemoState()
    demo.configure("2026-10-07", 1, 1, 2, False, "")

    def fail(_data):
        raise OSError("cannot save")

    monkeypatch.setattr(demo, "_save_coordinator", fail)
    assert not demo.addIngredientToGroceries(0, 0)
    assert not demo._coordinator_data.groceries
