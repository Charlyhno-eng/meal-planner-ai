"""Exercise every preview screen and modal with a real QML engine."""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject, QPoint, Qt
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from meal_planner_ai.ui import app
from meal_planner_ai.ui.demo import DemoState


def test_application_starts_main_window_maximized(monkeypatch):
    state = type(
        "State",
        (),
        {"assistant": type("Assistant", (), {"connect_shutdown": lambda self: None})()},
    )()
    window = type(
        "Window",
        (),
        {"showMaximized": lambda self: setattr(self, "maximized", True)},
    )()

    class FakeApplication:
        def __init__(self, _args):
            pass

        def setApplicationName(self, _name):
            pass

        def exec(self):
            return 0

    class FakeEngine:
        def __init__(self):
            pass

        def setInitialProperties(self, _properties):
            pass

        def load(self, _path):
            pass

        def rootObjects(self):
            return [window]

    monkeypatch.setattr(app, "QGuiApplication", FakeApplication)
    monkeypatch.setattr(
        app, "QQuickStyle", type("Style", (), {"setStyle": lambda _style: None})
    )
    monkeypatch.setattr(app, "QQmlApplicationEngine", FakeEngine)
    monkeypatch.setattr(app, "DemoState", lambda *_args, **_kwargs: state)

    assert app.main() == 0
    assert window.maximized


def visual_child(item: QQuickItem, name: str):
    if item.objectName() == name:
        return item
    for child in item.childItems():
        found = visual_child(child, name)
        if found is not None:
            return found
    return None


def test_desktop_navigation_and_dialogs(qt_app):
    demo = DemoState()
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(str(error) for error in errors)
    )
    engine.setInitialProperties({"demo": demo})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    assert len(engine.rootObjects()) == 1, warnings
    window = engine.rootObjects()[0]
    window.setWidth(960)
    window.setHeight(700)
    QTest.qWait(30)

    try:
        assert window.property("currentPage") == 5
        settings_nav = visual_child(window.contentItem(), "nav4")
        agents_nav = visual_child(window.contentItem(), "nav6")
        settings_top = settings_nav.mapToScene(QPoint(0, 0)).y()
        agents_bottom = agents_nav.mapToScene(QPoint(0, 48)).y()
        assert settings_top > agents_bottom
        assert settings_top + settings_nav.height() >= window.height() - 30
        assert window.findChild(QObject, "planningRequest") is not None
        for index in range(7):
            nav = visual_child(window.contentItem(), f"nav{index}")
            position = nav.mapToScene(QPoint(20, 20))
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, position.toPoint())
            qt_app.processEvents()
            assert window.property("currentPage") == index

        status = window.findChild(QObject, "agentInteractionsStatus")
        assert status.property("text").startswith(
            "Orchestrateur, planification, préférences et courses actifs."
        )
        QTest.keyClick(window, Qt.Key_1, Qt.ControlModifier)
        QTest.keyClick(window, Qt.Key_7, Qt.ControlModifier)
        assert window.property("currentPage") == 6

        # The reserve can filter to an empty result and recover.
        search = window.findChild(QObject, "pantrySearch")
        search.setProperty("text", "absent")
        qt_app.processEvents()
        search.setProperty("text", "")

        window.setProperty("currentPage", 2)
        qt_app.processEvents()
        row = visual_child(window.contentItem(), "grocery-Avocat|pièce")
        position = row.mapToScene(QPoint(130, 30))
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, position.toPoint())
        assert next(item for item in demo.groceries if item["name"] == "Avocat")[
            "checked"
        ]
        qt_app.processEvents()
        row = visual_child(window.contentItem(), "grocery-Avocat|pièce")
        position = row.mapToScene(QPoint(24, 30))
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, position.toPoint())
        assert not next(item for item in demo.groceries if item["name"] == "Avocat")[
            "checked"
        ]

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
            assert QMetaObject.invokeMethod(dialog, "open")
            QTest.qWait(20)
            assert dialog.property("visible")
            QTest.keyClick(window, Qt.Key_Escape)
            QTest.qWait(20)
            assert not dialog.property("visible")

        planning = window.findChild(QObject, "planningDialog")
        QMetaObject.invokeMethod(planning, "open")
        QTest.qWait(20)
        picker = window.findChild(QObject, "startDatePicker")
        picker.setProperty("iso", "2026-10-07")
        QMetaObject.invokeMethod(picker, "clicked")
        QTest.qWait(20)
        day = visual_child(window.contentItem(), "calendarDay-2026-10-14")
        assert day is not None
        position = day.mapToScene(QPoint(12, 12))
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, position.toPoint())
        assert picker.property("iso") == "2026-10-14"
        QMetaObject.invokeMethod(planning, "close")

        # Update all screen bindings, including the open recipe, after mutations.
        demo.replaceMeal(0)
        demo.setGuests(0, 2)
        demo.saveFood(-1, "Quinoa", 300, "g", "Épicerie")
        demo.toggleGrocery("Citron|pièce")
        demo.configure("2026-10-07", 14, 28, 4, True, "champignons")
        qt_app.processEvents()
        window.setWidth(1440)
        window.setHeight(960)
        qt_app.processEvents()
        assert not warnings, "\n".join(warnings)
    finally:
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


pytestmark = pytest.mark.usefixtures("sample_session")


@pytest.mark.parametrize("language,width,height", [("fr", 960, 700), ("en", 1280, 880)])
def test_home_shortcuts_and_live_summaries(qt_app, tmp_path, language, width, height):
    demo = DemoState(config_path=tmp_path / "config.toml")
    demo.setLanguage(language)
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(str(e) for e in errors))
    engine.setInitialProperties({"demo": demo})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    assert len(engine.rootObjects()) == 1, warnings
    window = engine.rootObjects()[0]
    window.setWidth(width)
    window.setHeight(height)
    QTest.qWait(200)

    def click(item):
        position = item.mapToScene(QPoint(10, 10))
        QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, position.toPoint())
        qt_app.processEvents()

    try:
        meals = visual_child(window.contentItem(), "mealOverview")
        pantry = visual_child(window.contentItem(), "pantryOverview")
        groceries = visual_child(window.contentItem(), "groceryOverview")
        pending = [item for item in demo.groceries if not item["available"]]
        assert meals.property("count") == len(demo.meals)
        assert pantry.property("count") == len(demo.pantry)
        assert groceries.property("count") == len(pending)

        # The main action remains on screen even at the minimum window size.
        send = visual_child(window.contentItem(), "generatePlanButton")
        bottom = send.mapToScene(QPoint(0, 0)).y() + send.height()
        assert bottom <= height - 24
        assert not send.property("enabled")
        before = demo.planning_context()
        click(visual_child(window.contentItem(), "requestExample2"))
        request = window.findChild(QObject, "planningRequest")
        assert request.property("text") == demo.translate("J’ai 500 g de riz.")
        assert request.property("activeFocus")
        assert send.property("enabled")
        assert not demo.assistant.busy
        assert demo.planning_context() == before

        demo.saveFood(-1, "Quinoa", 300, "g", "Épicerie")
        pending = [item for item in demo.groceries if not item["available"]]
        qt_app.processEvents()
        assert groceries.property("count") == len(pending)
        demo.toggleGrocery(pending[0]["id"])
        qt_app.processEvents()
        assert pantry.property("count") == len(demo.pantry)
        assert groceries.property("count") == len(pending) - 1
        assert visual_child(window.contentItem(), "nav2").property("count") == (
            len(pending) - 1
        )

        for card, index in ((meals, 0), (pantry, 1), (groceries, 2)):
            click(card)
            assert window.property("currentPage") == index
            assert visual_child(window.contentItem(), f"nav{index}").property(
                "selected"
            )
            QTest.keyClick(window, Qt.Key_1, Qt.ControlModifier)
            QTest.qWait(200)
        assert request.property("text") == demo.translate("J’ai 500 g de riz.")
        assert not warnings, "\n".join(warnings)
    finally:
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
