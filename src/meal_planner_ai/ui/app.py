"""Desktop application entry point."""

import sys
from pathlib import Path

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from meal_planner_ai.ui.demo import DemoState


def main() -> int:
    """Load the initial QML window and run the Qt event loop."""
    app = QGuiApplication(sys.argv)
    app.setApplicationName("Meal Planner AI")
    QQuickStyle.setStyle("Basic")
    engine = QQmlApplicationEngine()
    demo = DemoState(engine, config_path=Path.cwd() / "config.toml")
    demo.assistant.connect_shutdown()
    engine.setInitialProperties({"demo": demo})
    engine.load(Path(__file__).parent / "qml" / "Main.qml")
    if not engine.rootObjects():
        return 1
    engine.rootObjects()[0].showMaximized()
    return app.exec()
