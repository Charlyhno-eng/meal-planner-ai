"""User-facing recovery, validation and accessibility interactions."""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject, Qt
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from test_bootstrap import visual_child

from src.ui import app
from src.ui.demo import DemoState


@pytest.fixture
def desktop(qt_app, tmp_path):
    state = DemoState(config_path=tmp_path / "config.toml")
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(str(e) for e in errors))
    engine.setInitialProperties({"demo": state})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    assert engine.rootObjects(), warnings
    window = engine.rootObjects()[0]
    window.setWidth(960)
    window.setHeight(700)
    QTest.qWait(200)
    yield state, window
    window.close()
    engine.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    assert not warnings, "\n".join(warnings)


def test_empty_pages_offer_working_recovery_actions(desktop, qt_app):
    state, window = desktop
    window.setProperty("currentPage", 1)
    search = window.findChild(QObject, "pantrySearch")
    search.setProperty("text", "missing")
    qt_app.processEvents()
    empty = visual_child(window.contentItem(), "pantryEmptyState")
    assert empty.property("title") == "Aucun aliment trouvé"
    QMetaObject.invokeMethod(empty, "activated")
    assert search.property("text") == ""
    qt_app.processEvents()
    assert empty.property("title") == "Votre réserve est vide"
    QMetaObject.invokeMethod(empty, "activated")
    assert window.findChild(QObject, "foodDialog").property("visible")
    QTest.keyClick(window, Qt.Key_Escape)

    window.setProperty("currentPage", 2)
    qt_app.processEvents()
    empty = visual_child(window.contentItem(), "groceryEmptyState")
    QMetaObject.invokeMethod(empty, "activated")
    assert window.property("currentPage") == 5
    state.setLanguage("en")
    qt_app.processEvents()
    assert empty.property("actionText") == "Add purchases"


def test_food_quantity_validation_matches_storage_limits(desktop, qt_app):
    state, window = desktop
    dialog = window.findChild(QObject, "foodDialog")
    QMetaObject.invokeMethod(dialog, "open")
    QTest.qWait(20)
    name = window.findChild(QObject, "foodName")
    amount = window.findChild(QObject, "foodAmount")
    save = visual_child(dialog.property("contentItem"), "saveFoodButton")
    name.setProperty("text", "Rice")
    for value, valid in (
        ("0", False),
        ("-1", False),
        ("abc", False),
        ("Infinity", False),
        ("1e3", False),
        ("100001", False),
        ("100000", True),
        ("1,5", True),
        ("1.5", True),
    ):
        amount.setProperty("text", value)
        qt_app.processEvents()
        assert save.property("enabled") is valid, value
    QMetaObject.invokeMethod(save, "clicked")
    assert not dialog.property("visible")
    assert state.pantry[0]["amount"] == 1.5


def test_dialog_feedback_and_motion_preference(desktop, qt_app):
    state, window = desktop
    dialog = window.findChild(QObject, "planningDialog")
    QMetaObject.invokeMethod(dialog, "open")
    QTest.qWait(20)
    assert not state.configure("invalid", 7, 7, 2, False, "")
    qt_app.processEvents()
    assert dialog.property("visible")
    assert "date valide" in dialog.property("feedback")
    # The save footer remains inside the window when feedback increases the header.
    footer = dialog.property("footer")
    assert footer.mapToScene(footer.boundingRect().bottomRight()).y() <= 700
    QTest.keyClick(window, Qt.Key_Escape)
    QMetaObject.invokeMethod(dialog, "open")
    assert dialog.property("feedback") == ""
    QTest.keyClick(window, Qt.Key_Escape)

    window.setProperty("currentPage", 4)
    button = visual_child(window.contentItem(), "reduceMotionButton")
    button.forceActiveFocus()
    QTest.keyClick(window, Qt.Key_Space)
    qt_app.processEvents()
    assert button.property("checked")
    window.setProperty("currentPage", 6)
    qt_app.processEvents()
    toggle = visual_child(window.contentItem(), "agentAnimationToggle")
    assert not toggle.property("enabled")
    pulse = visual_child(window.contentItem(), "agentFlowPulse0")
    before = pulse.property("progress")
    QTest.qWait(100)
    assert pulse.property("progress") == before
    window.setProperty("currentPage", 4)
    button.forceActiveFocus()
    QTest.keyClick(window, Qt.Key_Space)
    qt_app.processEvents()
    assert not button.property("checked")
