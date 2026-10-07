"""Language persistence and translations preserve the preview's data identities."""

import tomllib
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject, QPoint, Qt
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from sample_data import RECIPES
from test_bootstrap import visual_child

from meal_planner_ai.ui import app
from meal_planner_ai.ui.demo import DemoState
from meal_planner_ai.ui.i18n import ENGLISH


def test_language_persists_and_restores(tmp_path):
    path = tmp_path / "config.toml"
    demo = DemoState(config_path=path)
    assert demo.language == "fr"
    assert tomllib.loads(path.read_text()) == {"application": {"language": "fr"}}
    assert demo.setLanguage("en")
    restored = DemoState(config_path=path)
    assert restored.language == "en"
    assert restored.meals[0]["title"] == "Roasted vegetable bowl"
    assert not restored.setLanguage("de")
    assert tomllib.loads(path.read_text())["application"]["language"] == "en"


@pytest.mark.parametrize(
    "content",
    [
        "[invalid",
        '[application]\nlanguage = "de"',
        "application = []",
    ],
)
def test_invalid_config_uses_french_without_overwriting_file(tmp_path, content):
    path = tmp_path / "config.toml"
    path.write_text(content)
    demo = DemoState(config_path=path)
    assert demo.language == "fr"
    assert demo.configError
    assert path.read_text() == content
    assert demo.setLanguage("en")
    assert not demo.configError
    assert tomllib.loads(path.read_text())["application"]["language"] == "en"


def test_failed_save_preserves_previous_language_and_config(tmp_path, monkeypatch):
    path = tmp_path / "config.toml"
    demo = DemoState(config_path=path)
    previous = path.read_text()

    def fail_replace(*args):
        raise PermissionError("Read-only directory")

    monkeypatch.setattr("meal_planner_ai.storage.config.os.replace", fail_replace)
    assert not demo.setLanguage("en")
    assert demo.language == "fr"
    assert demo.configError
    assert path.read_text() == previous
    assert list(tmp_path.iterdir()) == [path]


def test_all_recipe_content_is_translated_and_state_survives_language_change(qt_app):
    demo = DemoState()
    demo.configure("2026-10-07", 7, 7, 2, False, "")
    demo.setGuests(0, 2)
    assert demo.addIngredientToGroceries(0, 0)
    demo.toggleGrocery(demo.groceries[0]["id"])
    before = [(meal["id"], meal["art"], meal["servings"]) for meal in demo.meals]
    purchases = {
        (item["id"], item["available"], item["checked"]) for item in demo.groceries
    }
    demo.setLanguage("en")
    for recipe, meal in zip(RECIPES, demo.meals, strict=True):
        assert meal["title"] == ENGLISH[recipe["title"]]
        assert meal["subtitle"] == ENGLISH[recipe["subtitle"]]
        assert meal["steps"] == [ENGLISH[step] for step in recipe["steps"]]
        assert [item["name"] for item in meal["ingredients"]] == [
            ENGLISH[item[0]] for item in recipe["ingredients"]
        ]
    assert [
        (meal["id"], meal["art"], meal["servings"]) for meal in demo.meals
    ] == before
    assert {
        (item["id"], item["available"], item["checked"]) for item in demo.groceries
    } == purchases
    assert demo.meals[0]["label"] == "Meal 1"
    assert demo.period == "7 October — 13 October"
    demo.copyGroceries()
    assert qt_app.clipboard().text().startswith("Groceries\n")
    assert "✓ Quinoa" in qt_app.clipboard().text()
    rice = next(food for food in demo.pantry if food["name"] == "Rice")
    assert demo.saveFood(rice["id"], "Rice", 1000, "g", "Épicerie")
    assert (
        next(food for food in demo.pantry if food["id"] == rice["id"])["name"] == "Rice"
    )
    assert demo.configure("2026-10-07", 7, 7, 2, False, "mushrooms, salmon")
    assert not any(item["name"] in ("Mushrooms", "Salmon") for item in demo.groceries)
    demo.setLanguage("fr")
    assert (
        next(food for food in demo.pantry if food["id"] == rice["id"])["name"] == "Riz"
    )


@pytest.mark.parametrize("initial_language", ["fr", "en"])
def test_settings_switches_every_screen_and_dialog_without_qml_warnings(
    qt_app, tmp_path, initial_language
):
    path = tmp_path / "config.toml"
    DemoState(config_path=path).setLanguage(initial_language)
    demo = DemoState(config_path=path)
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(str(error) for error in errors)
    )
    engine.setInitialProperties({"demo": demo})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    assert len(engine.rootObjects()) == 1, warnings
    window = engine.rootObjects()[0]
    assert window.property("pageTitles").toVariant()[4] == (
        "Settings" if initial_language == "en" else "Paramètres"
    )
    window.setWidth(960)
    window.setHeight(700)
    try:
        window.setProperty("currentPage", 4)
        QTest.qWait(20)
        english = visual_child(window.contentItem(), "languageEnglish")
        position = english.mapToScene(QPoint(20, 20))
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, position.toPoint())
        qt_app.processEvents()
        assert demo.language == "en"
        assert window.property("pageTitles").toVariant() == [
            "My meal plan",
            "My pantry",
            "My groceries",
            "My household",
            "Settings",
            "Plan with AI",
            "AI interactions",
        ]
        assert tomllib.loads(path.read_text())["application"]["language"] == "en"
        for index in range(7):
            window.setProperty("currentPage", index)
            qt_app.processEvents()
        for name in [
            "planningDialog",
            "preferencesDialog",
            "foodDialog",
            "guestDialog",
            "recipeDialog",
        ]:
            dialog = window.findChild(QObject, name)
            if name == "recipeDialog":
                dialog.setProperty("mealId", 0)
            QMetaObject.invokeMethod(dialog, "open")
            QTest.qWait(20)
            if name == "planningDialog":
                picker = window.findChild(QObject, "startDatePicker")
                picker.setProperty("iso", "2026-10-07")
                assert "Wednesday" in picker.property("text")
                assert "October" in picker.property("text")
            QMetaObject.invokeMethod(dialog, "close")
        assert (
            window.findChild(QObject, "recipeDialog").property("title")
            == "Time to cook"
        )
        window.setProperty("currentPage", 4)
        french = visual_child(window.contentItem(), "languageFrench")
        position = french.mapToScene(QPoint(20, 20))
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, position.toPoint())
        qt_app.processEvents()
        assert demo.language == "fr"
        assert (
            window.findChild(QObject, "recipeDialog").property("title") == "À cuisiner"
        )
        assert not warnings, "\n".join(warnings)
    finally:
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


pytestmark = pytest.mark.usefixtures("sample_session")
