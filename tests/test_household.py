"""Household profiles persist and constrain planning without partial updates."""

import json
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject, Qt
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from test_bootstrap import visual_child

from src.agents.food_preferences import (
    PreferenceConflict,
    check_preferences,
)
from src.models.coordinator import (
    CoordinatorProposal,
    Period,
    RequestedMeal,
)
from src.models.recipes import Ingredient, Recipe
from src.ui import app
from src.ui.demo import DemoState

PROFILES = [
    {"name": "Alice", "foods_to_avoid": "lactose"},
    {"name": "Bob", "foods_to_avoid": "gluten, salmon"},
]


def test_profiles_persist_resize_and_remain_in_planning_context(qt_app, tmp_path):
    path = tmp_path / "config.toml"
    state = DemoState(config_path=path)
    assert state.setHousehold(PROFILES, True, "mushrooms")
    restored = DemoState(config_path=path)
    assert restored.settings["members"] == PROFILES
    assert restored.settings["vegetarian"]
    assert restored.settings["foods_to_avoid"] == "mushrooms"
    assert restored.planning_context()["settings"]["members"] == PROFILES
    # A consumer cannot edit the live profiles through a returned settings map.
    restored.settings["members"][0]["name"] = "Changed"
    assert restored.settings["members"] == PROFILES
    assert restored.configure("2026-10-07", 7, 7, 3, True, "mushrooms")
    assert restored.settings["members"] == PROFILES + [
        {"name": "", "foods_to_avoid": ""}
    ]
    assert restored.configure("2026-10-07", 7, 7, 1, True, "mushrooms")
    assert DemoState(config_path=path).settings["members"] == PROFILES[:1]


def test_legacy_household_preferences_load_into_unified_food_lists(qt_app, tmp_path):
    config_path = tmp_path / "config.toml"
    household_path = tmp_path / "data" / "household.json"
    household_path.parent.mkdir()
    household_path.write_text(
        json.dumps(
            {
                "people": 1,
                "members": [{"name": "Alice", "intolerances": "lactose"}],
                "guest_groups": [],
                "vegetarian": False,
                "dislikes": "mushrooms",
            }
        )
    )

    state = DemoState(config_path=config_path)

    assert not state.householdError
    assert state.settings["members"] == [{"name": "Alice", "foods_to_avoid": "lactose"}]
    assert state.settings["foods_to_avoid"] == "mushrooms"
    assert state.setHousehold(
        state.settings["members"],
        state.settings["vegetarian"],
        state.settings["foods_to_avoid"],
    )
    saved = json.loads(household_path.read_text())
    assert saved["members"] == [{"name": "Alice", "foods_to_avoid": "lactose"}]
    assert saved["foods_to_avoid"] == "mushrooms"
    assert "intolerances" not in household_path.read_text()
    assert "dislikes" not in household_path.read_text()


@pytest.mark.parametrize(
    "profiles",
    [
        [],
        PROFILES * 7,
        [{"name": "a" * 101}],
        [{"name": "Alice", "foods_to_avoid": "x" * 1001}],
    ],
)
def test_invalid_profiles_preserve_state(qt_app, profiles):
    state = DemoState()
    previous = state.planning_context()
    assert not state.setHousehold(profiles, False, "")
    assert state.planning_context() == previous


def test_household_save_failure_preserves_profiles_and_file(
    qt_app, tmp_path, monkeypatch
):
    state = DemoState(config_path=tmp_path / "config.toml")
    assert state.setHousehold(PROFILES, False, "")
    path = tmp_path / "data" / "household.json"
    previous = path.read_text()

    def fail(*_args):
        raise OSError("read only")

    monkeypatch.setattr("src.storage.household.os.replace", fail)
    assert not state.setHousehold([{"name": "New", "foods_to_avoid": ""}], False, "")
    assert state.settings["members"] == PROFILES
    assert path.read_text() == previous
    assert list(path.parent.iterdir()) == [path]


def test_invalid_household_is_reported_and_not_overwritten(qt_app, tmp_path):
    path = tmp_path / "data" / "household.json"
    path.parent.mkdir()
    path.write_text('{"people": 2, "members": []}')
    state = DemoState(config_path=tmp_path / "config.toml")
    assert state.householdError
    assert not state.setHousehold(PROFILES, False, "")
    assert path.read_text() == '{"people": 2, "members": []}'


@pytest.mark.parametrize("food", ["Mascarpone", "Bread", "Saumon"])
def test_each_person_food_exclusion_rejects_recipes_and_purchases(qt_app, food):
    state = DemoState()
    assert state.setHousehold(PROFILES, False, "")
    meal = RequestedMeal(
        title="Test",
        servings=2,
        period=Period(start="2026-10-07", end="2026-10-07"),
        recipe=Recipe(
            title="Test",
            servings=2,
            subtitle="Test",
            minutes=10,
            vegetarian=True,
            ingredients=[
                Ingredient(name=food, amount=100, unit="g", category="Épicerie")
            ],
            steps=["Prepare the dish."],
        ),
    )
    with pytest.raises(PreferenceConflict):
        check_preferences([meal], state.settings)
    proposal = CoordinatorProposal(
        actions=[
            dict(
                service="grocery_add",
                name=food,
                amount=100.0,
                unit="g",
                category="Épicerie",
            )
        ]
    )
    before = state.planning_context()
    with pytest.raises(ValueError, match="excluded food"):
        state.apply_commands(proposal)
    assert state.planning_context() == before


@pytest.mark.parametrize("language", ["fr", "en"])
def test_household_dialog_edits_saves_and_cancels(qt_app, tmp_path, language):
    state = DemoState(config_path=tmp_path / "config.toml")
    state.setLanguage(language)
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(str(e) for e in errors))
    engine.setInitialProperties({"demo": state})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    assert engine.rootObjects(), warnings
    window = engine.rootObjects()[0]
    window.setWidth(960)
    window.setHeight(700)
    try:
        window.setProperty("currentPage", 3)
        dialog = window.findChild(QObject, "preferencesDialog")
        QMetaObject.invokeMethod(dialog, "open")
        QTest.qWait(200)
        content = dialog.property("contentItem")
        for name, value in [
            ("memberName-0", "Alice"),
            ("memberName-1", "Bob"),
        ]:
            field = visual_child(content, name)
            assert field is not None, warnings
            field.forceActiveFocus()
            field.setProperty("text", value)
            QMetaObject.invokeMethod(field, "textEdited")
        field = visual_child(content, "excludedFoodInput")
        field.setProperty("text", "lactose")
        QMetaObject.invokeMethod(visual_child(content, "addExcludedFood"), "clicked")
        field.setProperty("text", " Lactose ")
        QMetaObject.invokeMethod(field, "accepted")
        tags = visual_child(content, "householdExclusions")
        assert tags.property("items").toVariant() == ["lactose"]
        assert QMetaObject.invokeMethod(
            visual_child(content, "saveHousehold"), "clicked"
        )
        qt_app.processEvents()
        assert state.settings["members"][0] == {"name": "Alice", "foods_to_avoid": ""}
        assert state.settings["foods_to_avoid"] == "lactose"
        assert state.settings["members"][1]["name"] == "Bob"
        QMetaObject.invokeMethod(dialog, "open")
        QTest.qWait(200)
        field = visual_child(content, "memberName-0")
        field.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
        field.setProperty("text", "Discarded")
        QMetaObject.invokeMethod(field, "textEdited")
        QMetaObject.invokeMethod(dialog, "close")
        assert state.settings["members"][0] == {"name": "Alice", "foods_to_avoid": ""}
        assert state.settings["foods_to_avoid"] == "lactose"
        QMetaObject.invokeMethod(dialog, "open")
        QTest.qWait(200)
        people = visual_child(content, "householdPeople")
        people.setProperty("value", 12)
        QMetaObject.invokeMethod(people, "valueModified")
        qt_app.processEvents()
        assert visual_child(content, "memberName-11") is not None
        button = visual_child(content, "saveHousehold")
        assert (
            button.mapToScene(button.boundingRect().bottomRight()).y() < window.height()
        )
        QMetaObject.invokeMethod(button, "clicked")
        assert state.settings["people"] == 12
        assert state.settings["members"][0] == {"name": "Alice", "foods_to_avoid": ""}
        assert state.settings["foods_to_avoid"] == "lactose"
        assert not warnings, "\n".join(warnings)
    finally:
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


def test_catalogue_planning_preserves_profiles_and_checks_foods_to_avoid(
    qt_app, sample_session, tmp_path
):
    from src.models.planning import PlanningProposal

    state = DemoState(config_path=tmp_path / "config.toml")
    profiles = [{"name": "Alice", "foods_to_avoid": "salmon"}]
    assert state.setHousehold(profiles, False, "")
    settings = {key: value for key, value in state.settings.items() if key != "members"}
    settings["count"] = 1
    salmon = next(
        i for i, r in enumerate(state.recipe_catalogue) if not r["vegetarian"]
    )
    proposal = PlanningProposal(
        settings=settings, recipe_ids=[salmon], pantry_updates=[], guests=[]
    )
    before = state.planning_context()
    with pytest.raises(ValueError, match="excluded ingredient"):
        state.apply_proposal(proposal)
    assert state.planning_context() == before
    proposal.recipe_ids = [0]
    state.apply_proposal(proposal)
    assert state.settings["members"] == profiles
    assert (
        DemoState(config_path=tmp_path / "config.toml").settings["members"] == profiles
    )


def test_guest_groups_persist_before_planning_and_keep_individual_exclusions(
    qt_app, tmp_path
):
    state = DemoState(config_path=tmp_path / "config.toml")
    assert not state.meals
    assert state.addGuestGroup("Friends", [0, 2], PROFILES)
    assert state.addGuestGroup("Family", [1], [{"name": "Eve"}])
    restored = DemoState(config_path=tmp_path / "config.toml")
    groups = restored.settings["guest_groups"]
    assert groups[0] == dict(name="Friends", meals=[0, 2], members=PROFILES)
    assert groups[1]["members"][0]["name"] == "Eve"
    assert restored.planning_context()["settings"]["guest_groups"] == groups
    assert restored.setHousehold([{"name": "Resident"}], False, "")
    assert restored.settings["guest_groups"] == groups
    assert restored.removeGuestGroup(0)
    assert (
        len(DemoState(config_path=tmp_path / "config.toml").settings["guest_groups"])
        == 1
    )


def test_guest_groups_scale_selected_meals_and_groceries(qt_app, sample_session):
    state = DemoState()
    before = state._planned_ingredients()
    assert state.addGuestGroup("Friends", [0, 2], [{"name": "Eve"}])
    assert state.addGuestGroup("Family", [2], [{"name": "Jo"}])
    assert [meal["guests"] for meal in state.meals[:4]] == [1, 0, 2, 0]
    assert [meal["servings"] for meal in state.meals[:4]] == [3, 2, 4, 2]
    assert state._planned_ingredients()[0].amount == before[0].amount * 1.5
    assert state.removeGuestGroup(0)
    assert [meal["guests"] for meal in state.meals[:4]] == [0, 0, 1, 0]


@pytest.mark.parametrize(
    "meals, members", [([], PROFILES), ([0, 0], PROFILES), ([-1], PROFILES), ([0], [])]
)
def test_invalid_guest_groups_do_not_mutate_state(qt_app, meals, members):
    state = DemoState()
    before = state.planning_context()
    assert not state.addGuestGroup("Invalid", meals, members)
    assert state.planning_context() == before


def test_guest_save_failure_preserves_state(qt_app, tmp_path, monkeypatch):
    state = DemoState(config_path=tmp_path / "config.toml")
    assert state.addGuestGroup("Friends", [0], PROFILES)
    before = state.planning_context()

    def fail(*_args):
        raise OSError("read only")

    monkeypatch.setattr("src.storage.household.os.replace", fail)
    assert not state.addGuestGroup("Family", [1], PROFILES)
    assert not state.removeGuestGroup(0)
    assert state.planning_context() == before


@pytest.mark.parametrize("language", ["fr", "en"])
def test_household_add_button_and_guest_dialog_work_without_meals(
    qt_app, tmp_path, language
):
    state = DemoState(config_path=tmp_path / "config.toml")
    state.setLanguage(language)
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(str(e) for e in errors))
    engine.setInitialProperties({"demo": state})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    window = engine.rootObjects()[0]
    window.setWidth(960)
    window.setHeight(700)
    try:
        window.setProperty("currentPage", 3)
        dialog = window.findChild(QObject, "preferencesDialog")
        QMetaObject.invokeMethod(dialog, "open")
        QTest.qWait(200)
        content = dialog.property("contentItem")
        people = visual_child(content, "householdPeople")
        # Exercise the actual plus indicator, not a programmatic value change.
        point = people.mapToScene(people.boundingRect().center())
        point.setX(point.x() + people.width() / 2 - 20)
        QTest.mouseClick(window, Qt.LeftButton, pos=point.toPoint())
        qt_app.processEvents()
        assert people.property("value") == 3
        assert visual_child(content, "memberName-2") is not None
        field = visual_child(content, "memberFoodsToAvoid-0")
        assert field is not None
        assert field.property("placeholderText") == (
            "Aliments que cette personne ne veut pas manger (séparés par des virgules)"
            if language == "fr"
            else "Foods this person does not want to eat (comma-separated)"
        )
        assert visual_child(content, "memberIntolerances-0") is None
        field.setProperty("text", "lactose")
        QMetaObject.invokeMethod(field, "textEdited")
        QMetaObject.invokeMethod(visual_child(content, "saveHousehold"), "clicked")
        assert state.settings["members"][0]["foods_to_avoid"] == "lactose"
        QTest.qWait(200)
        button = visual_child(window.contentItem(), "addGuestGroupButton")
        assert button.property("enabled")
        QMetaObject.invokeMethod(button, "clicked")
        QTest.qWait(200)
        guest_dialog = window.findChild(QObject, "guestDialog")
        assert guest_dialog.property("visible")
        content = guest_dialog.property("contentItem")
        for index in (0, 2):
            QMetaObject.invokeMethod(
                visual_child(content, f"guestMeal-{index}"), "clicked"
            )
        for name, value in [("guestName-0", "Eve"), ("guestFoodsToAvoid-0", "gluten")]:
            field = visual_child(content, name)
            field.setProperty("text", value)
            QMetaObject.invokeMethod(field, "textEdited")
        QMetaObject.invokeMethod(visual_child(content, "saveGuestGroup"), "clicked")
        assert not guest_dialog.property("visible")
        group = state.settings["guest_groups"][0]
        assert group["meals"] == [0, 2]
        assert group["members"][0] == {"name": "Eve", "foods_to_avoid": "gluten"}
        QMetaObject.invokeMethod(guest_dialog, "open")
        QTest.qWait(200)
        QMetaObject.invokeMethod(guest_dialog, "close")
        assert len(state.settings["guest_groups"]) == 1
        assert not warnings, "\n".join(warnings)
    finally:
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


def test_guest_exclusions_reject_future_recipes_and_scale_workflow_groceries(qt_app):
    from src.workflow.meal_request import calculate_execution_groceries

    state = DemoState()
    assert state.addGuestGroup(
        "Friends", [0], [{"name": "Eve", "foods_to_avoid": "lactose"}]
    )
    meal = RequestedMeal(
        title="Dish",
        servings=2,
        period=Period(start="2026-10-07", end="2026-10-07"),
        recipe=Recipe(
            title="Dish",
            servings=2,
            subtitle="Dish",
            minutes=10,
            vegetarian=True,
            ingredients=[
                Ingredient(
                    name="Milk", amount=100, unit="ml", category="Produits frais"
                )
            ],
            steps=["Mix."],
        ),
    )
    with pytest.raises(PreferenceConflict):
        check_preferences([meal], state.settings)
    meal.recipe.ingredients[0].name = "Water"
    commands = CoordinatorProposal(
        actions=[dict(service="meal_request", title="Dish", servings=2)]
    )
    groceries = calculate_execution_groceries(
        commands, [meal], state.planning_context()
    )
    assert groceries[0].required == 150
    state.apply_commands(commands, planned_meals=[meal])
    assert state.meals[0]["servings"] == 3
    assert state._planned_ingredients()[0].amount == 150
