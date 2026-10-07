"""Production session starts without demonstration data or fake agent results."""

from src.ui.demo import DemoState


def test_empty_session_and_manual_inputs(qt_app):
    state = DemoState()
    assert state.recipe_catalogue == []
    assert state.planning_context()["recipes"] == []
    assert state.pantry == state.meals == state.guests == state.groceries == []
    assert state.configure("2026-10-07", 3, 4, 2, True, "mushrooms")
    assert state.settings["dislikes"] == "mushrooms"
    assert state.meals == state.groceries == []
    assert not state.replaceMeal(0)
    state.setGuests(0, 2)
    assert state.guests == []
    assert state.saveFood(-1, "Apples", 3, "pièce", "Fruits & légumes")
    assert state.pantry[0]["id"] == 1
    assert state.groceries == []
    state.removeFood(1)
    assert state.pantry == []


def test_coordinator_without_key_does_not_start_inference(qt_app, monkeypatch):
    state = DemoState()

    def unexpected(*args):
        raise AssertionError("No inference should run without an API key")

    monkeypatch.setattr(state.assistant, "_run", unexpected)
    state.assistant.plan("Plan dinner")
    assert not state.assistant.busy
    assert state.assistant.proposal == {}
    assert state.assistant.error


def test_empty_desktop_screens_and_dialogs(qt_app):
    from pathlib import Path

    from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtTest import QTest

    from src.ui import app

    state = DemoState()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(str(e) for e in errors))
    engine.setInitialProperties({"demo": state})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    assert len(engine.rootObjects()) == 1, warnings
    window = engine.rootObjects()[0]
    try:
        for language in ("fr", "en"):
            state.setLanguage(language)
            for index in range(7):
                window.setProperty("currentPage", index)
                QTest.qWait(10)
            for name in (
                "planningDialog",
                "preferencesDialog",
                "foodDialog",
                "guestDialog",
                "recipeDialog",
            ):
                dialog = window.findChild(QObject, name)
                QMetaObject.invokeMethod(dialog, "open")
                QTest.qWait(10)
                if name == "planningDialog":
                    meals = window.findChild(QObject, "planningMealCount")
                    days = window.findChild(QObject, "planningDays")
                    assert meals.property("to") == 28
                    meals.setProperty("value", 10)
                    days.setProperty("value", 1)
                    assert meals.property("value") == 10
                QMetaObject.invokeMethod(dialog, "close")
        assert not warnings, "\n".join(warnings)
    finally:
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
