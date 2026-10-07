"""GLM credential persistence and password visibility."""

from pathlib import Path

from PySide6.QtCore import QCoreApplication, QEvent, QMetaObject, QObject
from PySide6.QtQml import QQmlApplicationEngine, QQmlExpression, qmlContext

from src.ui import app
from src.ui.demo import DemoState


def test_key_persistence_and_failed_save(tmp_path, monkeypatch):
    config = tmp_path / "config.toml"
    demo = DemoState(config_path=config)
    assert demo.setGlmApiKey(" test-secret ")
    assert DemoState(config_path=config).glmApiKey == "test-secret"
    assert demo.setLanguage("en")
    assert DemoState(config_path=config).glmApiKey == "test-secret"

    def fail(*args):
        raise PermissionError("read only")

    with monkeypatch.context() as patch:
        patch.setattr("src.storage.config.os.replace", fail)
        assert not demo.setGlmApiKey("replacement")
    assert demo.glmApiKey == "test-secret"
    assert demo.glmError
    assert DemoState(config_path=config).glmApiKey == "test-secret"
    assert demo.setGlmApiKey("")
    assert DemoState(config_path=config).glmApiKey == ""


def test_key_visibility_and_save(qt_app, tmp_path):
    demo = DemoState(config_path=tmp_path / "config.toml")
    demo.setGlmApiKey("test-secret")
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda errors: warnings.extend(map(str, errors)))
    engine.setInitialProperties({"demo": demo})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    window = engine.rootObjects()[0]
    try:
        window.setProperty("currentPage", 4)
        qt_app.processEvents()
        field = window.findChild(QObject, "glmApiKey")
        reveal = window.findChild(QObject, "glmRevealKey")
        save = window.findChild(QObject, "glmSaveKey")
        assert field.property("text") == "test-secret"
        assert (
            QQmlExpression(qmlContext(field), field, "Number(echoMode)").evaluate()[0]
            == 2
        )
        QMetaObject.invokeMethod(reveal, "click")
        assert (
            QQmlExpression(qmlContext(field), field, "Number(echoMode)").evaluate()[0]
            == 0
        )
        QMetaObject.invokeMethod(reveal, "click")
        assert (
            QQmlExpression(qmlContext(field), field, "Number(echoMode)").evaluate()[0]
            == 2
        )
        field.setProperty("text", "new-secret")
        QMetaObject.invokeMethod(save, "click")
        assert demo.glmApiKey == "new-secret"
        assert (
            QQmlExpression(qmlContext(field), field, "Number(echoMode)").evaluate()[0]
            == 2
        )
        assert not warnings, "\n".join(warnings)
    finally:
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
