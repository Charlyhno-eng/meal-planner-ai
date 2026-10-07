"""Household profiles persist and constrain planning without partial updates."""

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
    {"name": "Alice", "intolerances": "lactose"},
    {"name": "Bob", "intolerances": "gluten, salmon"},
]


def test_profiles_persist_resize_and_remain_in_planning_context(qt_app, tmp_path):
    path = tmp_path / "config.toml"
    state = DemoState(config_path=path)
    assert state.setHousehold(PROFILES, True, "mushrooms")
    restored = DemoState(config_path=path)
    assert restored.settings["members"] == PROFILES
    assert restored.settings["vegetarian"]
    assert restored.settings["dislikes"] == "mushrooms"
    assert restored.planning_context()["settings"]["members"] == PROFILES
    # A consumer cannot edit the live profiles through a returned settings map.
    restored.settings["members"][0]["name"] = "Changed"
    assert restored.settings["members"] == PROFILES
    assert restored.configure("2026-10-07", 7, 7, 3, True, "mushrooms")
    assert restored.settings["members"] == PROFILES + [{"name": "", "intolerances": ""}]
    assert restored.configure("2026-10-07", 7, 7, 1, True, "mushrooms")
    assert DemoState(config_path=path).settings["members"] == PROFILES[:1]


@pytest.mark.parametrize(
    "profiles",
    [
        [],
        PROFILES * 7,
        [{"name": "a" * 101}],
        [{"name": "Alice", "intolerances": "x" * 1001}],
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
    assert not state.setHousehold([{"name": "New", "intolerances": ""}], False, "")
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
def test_each_person_intolerance_rejects_recipes_and_purchases(qt_app, food):
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
            ("memberIntolerances-0", "lactose"),
            ("memberName-1", "Bob"),
        ]:
            field = visual_child(content, name)
            assert field is not None, warnings
            field.forceActiveFocus()
            field.setProperty("text", value)
            QMetaObject.invokeMethod(field, "textEdited")
        assert QMetaObject.invokeMethod(
            visual_child(content, "saveHousehold"), "clicked"
        )
        qt_app.processEvents()
        assert state.settings["members"][0] == PROFILES[0]
        assert state.settings["members"][1]["name"] == "Bob"
        QMetaObject.invokeMethod(dialog, "open")
        QTest.qWait(200)
        field = visual_child(content, "memberName-0")
        field.forceActiveFocus()
        QTest.keyClick(window, Qt.Key_A, Qt.ControlModifier)
        field.setProperty("text", "Discarded")
        QMetaObject.invokeMethod(field, "textEdited")
        QMetaObject.invokeMethod(dialog, "close")
        assert state.settings["members"][0] == PROFILES[0]
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
        assert state.settings["members"][0] == PROFILES[0]
        assert not warnings, "\n".join(warnings)
    finally:
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


def test_catalogue_planning_preserves_profiles_and_checks_intolerances(
    qt_app, sample_session, tmp_path
):
    from src.models.planning import PlanningProposal

    state = DemoState(config_path=tmp_path / "config.toml")
    profiles = [{"name": "Alice", "intolerances": "salmon"}]
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
