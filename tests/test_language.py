"""System language detection and translation coverage for the desktop UI."""

import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from sample_data import RECIPES
from test_bootstrap import visual_child

from src.domain.foods import canonical_food
from src.localization import CATALOGS, ENGLISH, system_language, translate
from src.localization.catalogs import CANONICAL_KEYS
from src.ui import app
from src.ui.demo import DemoState
from src.ui.i18n import translate_food


@pytest.mark.parametrize(
    "tags,expected",
    [
        (["fr-FR"], "fr"),
        (["fr-CA"], "fr"),
        (["en-US"], "en"),
        (["en_GB"], "en"),
        (["de-DE", "fr-CH", "en-US"], "fr"),
        (["en-AU", "fr-FR"], "en"),
        (["de-DE"], "en"),
        (["es-ES", "fr-FR", "en-GB"], "fr"),
        (["es-ES"], "en"),
        ([], "en"),
    ],
)
def test_system_ui_language_preference_order(monkeypatch, tags, expected):
    monkeypatch.setattr(
        "src.localization.system.QLocale",
        SimpleNamespace(system=lambda: SimpleNamespace(uiLanguages=lambda: tags)),
    )
    assert system_language() == expected


@pytest.mark.parametrize("language", ["fr", "en"])
@pytest.mark.parametrize(
    "content", [None, '[application]\nlanguage = "fr"', "[invalid"]
)
def test_startup_uses_system_language_without_reading_or_writing_preference(
    tmp_path, monkeypatch, language, content
):
    path = tmp_path / "config.toml"
    if content is not None:
        path.write_text(content)
    monkeypatch.setattr("src.ui.demo.system_language", lambda: language)
    state = DemoState(config_path=path)
    assert state.language == language
    assert state.planning_context()["language"] == language
    if content is None:
        assert not path.exists()
    else:
        assert path.read_text() == content


def test_application_text_ids_exist_in_both_catalogs():
    root = Path(app.__file__).parents[1]
    references = set()
    for path in [*root.rglob("*.qml"), *root.rglob("*.py")]:
        text = path.read_text()
        # Covers static calls as well as IDs in dynamic QML models/UI state.
        references.update(
            re.findall(
                r'["\']((?:text|month|prefix|suffix|category|unit|food|workflow|app|model|format)\.[a-z0-9_]+)["\']',
                text,
            )
        )
        if path.suffix == ".qml":
            # New static UI phrases must also use an ID, not a source sentence.
            references.update(re.findall(r'I18n\.tr\(\s*"([^"]+)"', text))
    references.update(CANONICAL_KEYS.values())
    for language, catalog in CATALOGS.items():
        assert not references - catalog.keys(), language


def test_catalogs_have_matching_keys_and_template_fields():
    from string import Formatter

    french, english = CATALOGS["fr"], CATALOGS["en"]
    assert french.keys() == english.keys()

    def fields(text):
        return {name for _, name, _, _ in Formatter().parse(text) if name is not None}

    for key in french:
        assert french[key] and english[key], key
        assert fields(french[key]) == fields(english[key]), key


def test_catalog_translation_preserves_domain_and_custom_values():
    assert translate("text.settings", "fr") == "Paramètres"
    assert translate("text.settings", "en") == "Settings"
    assert translate("text.settings", "es") == "Settings"
    assert translate("Riz", "en") == "Rice"
    assert translate("Ma recette {maison}", "en") == "Ma recette {maison}"
    assert "riz (100 g)" in translate(
        "workflow.ask_package_size", "fr", foods="riz (100 g)"
    )


def test_food_display_wording_keeps_persisted_identities(monkeypatch):
    monkeypatch.setitem(CATALOGS["fr"], "food.rice", "Riz (libellé modifié)")
    assert canonical_food("Rice") == "Riz"
    assert canonical_food("Riz (libellé modifié)") == "Riz"
    assert translate_food("Riz", "fr") == "Riz (libellé modifié)"
    assert translate_food("Mon mélange maison", "en") == "Mon mélange maison"


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
def test_system_language_translates_every_screen_and_dialog_without_qml_warnings(
    qt_app, tmp_path, monkeypatch, initial_language
):
    path = tmp_path / "config.toml"
    monkeypatch.setattr("src.ui.demo.system_language", lambda: initial_language)
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
        assert visual_child(window.contentItem(), "languageEnglish") is None
        assert visual_child(window.contentItem(), "languageFrench") is None
        demo.setLanguage("en")
        qt_app.processEvents()
        assert window.property("pageTitles").toVariant()[4] == "Settings"
        window.setProperty("currentPage", 3)
        qt_app.processEvents()
        assert (
            visual_child(window.contentItem(), "addExcludedFood").property("text")
            == "Add"
        )
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
        quantity_mode = window.findChild(QObject, "foodQuantityMode")
        assert quantity_mode.property("displayText") == "Total quantity"
        assert (
            window.findChild(QObject, "recipeDialog").property("title")
            == "Time to cook"
        )
        window.setProperty("currentPage", 4)
        demo.setLanguage("fr")
        qt_app.processEvents()
        assert demo.language == "fr"
        assert quantity_mode.property("displayText") == "Quantité totale"
        assert (
            window.findChild(QObject, "recipeDialog").property("title") == "À cuisiner"
        )
        assert not warnings, "\n".join(warnings)
    finally:
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


pytestmark = pytest.mark.usefixtures("sample_session")
