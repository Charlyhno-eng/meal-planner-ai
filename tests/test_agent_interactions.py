"""Exercise the agent map's selection, keyboard access, and window resizing."""

from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, Qt
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from test_bootstrap import visual_child

from meal_planner_ai.ui import app
from meal_planner_ai.ui.demo import DemoState


@pytest.mark.parametrize("size", [(960, 700), (1280, 880), (1440, 960)])
def test_agent_map_selection_keyboard_translation_and_geometry(qt_app, tmp_path, size):
    demo = DemoState(config_path=tmp_path / "config.toml")
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(
        lambda errors: warnings.extend(str(error) for error in errors)
    )
    engine.setInitialProperties({"demo": demo})
    engine.load(Path(app.__file__).parent / "qml" / "Main.qml")
    assert engine.rootObjects(), warnings
    window = engine.rootObjects()[0]
    window.setWidth(size[0])
    window.setHeight(size[1])
    window.setProperty("currentPage", 6)
    QTest.qWait(50)
    page = window.findChild(QObject, "agentInteractionsPage")
    graph = window.findChild(QObject, "agentGraph")
    connections = window.findChild(QObject, "agentConnections")
    user = visual_child(window.contentItem(), "userNode")
    link_labels = [
        visual_child(window.contentItem(), f"linkLabel{source}To{target}")
        for source, target in [
            ("user", "coordinator"),
            ("coordinator", "planning"),
            ("coordinator", "preferences"),
            ("coordinator", "groceries"),
            ("groceries", "verification"),
        ]
    ]
    title = window.findChild(QObject, "selectedAgentTitle")
    role = window.findChild(QObject, "selectedAgentRole")
    nodes = [visual_child(window.contentItem(), f"agentNode{i}") for i in range(5)]

    try:
        assert user is not None
        assert connections.property("linkPairs").toVariant() == [
            "user->coordinator",
            "coordinator->planning",
            "coordinator->preferences",
            "coordinator->groceries",
            "groceries->verification",
        ]
        assert title.property("text") == "Orchestrateur"

        # The full diagram remains visible at the minimum window size; nodes
        # neither overlap each other nor overflow the graph when resized.
        for width, height in [size, (960, 700), size]:
            window.setWidth(width)
            window.setHeight(height)
            QTest.qWait(30)
            bounds = []
            user_rect = user.mapRectToItem(graph, user.boundingRect())
            assert graph.boundingRect().contains(user_rect)
            assert user_rect.center().y() == pytest.approx(graph.height() / 2, abs=1)
            assert (
                user_rect.center().x()
                < nodes[0].mapRectToItem(graph, nodes[0].boundingRect()).center().x()
            )
            bounds.append(user_rect)
            for node in nodes:
                assert node is not None
                rect = node.mapRectToItem(graph, node.boundingRect())
                assert graph.boundingRect().contains(rect)
                assert node.mapToScene(QPoint(0, 0)).y() >= 0
                assert (
                    node.mapToScene(QPoint(0, int(node.height()))).y()
                    <= window.height()
                )
                assert not any(rect.intersects(other) for other in bounds)
                bounds.append(rect)
            for label in link_labels:
                assert label is not None
                label_rect = label.mapRectToItem(graph, label.boundingRect())
                assert graph.boundingRect().contains(label_rect)
                overlaps_node = any(
                    label_rect.intersects(node_rect) for node_rect in bounds
                )
                assert not overlaps_node, f"{label.objectName()} overlaps a node"

        for index, node in enumerate(nodes):
            position = node.mapToScene(QPoint(30, 30)).toPoint()
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, position)
            qt_app.processEvents()
            assert page.property("selectedAgent") == index
            assert title.property("text") == node.property("title")
            assert role.property("text")
            assert [n.property("selected") for n in nodes] == [
                i == index for i in range(5)
            ]

        # Switching language updates the selected node and inspector in place.
        assert demo.setLanguage("en")
        qt_app.processEvents()
        assert page.property("selectedAgent") == 4
        assert title.property("text") == "Grocery verification"
        assert role.property("text").startswith("Checks the grocery list")
        status = window.findChild(QObject, "agentInteractionsStatus")
        assert status.property("text").startswith("Orchestrator active for requests.")

        nodes = [visual_child(window.contentItem(), f"agentNode{i}") for i in range(5)]
        nodes[0].forceActiveFocus()
        QTest.keyClick(window, Qt.Key_Tab)
        assert nodes[1].hasActiveFocus()
        QTest.keyClick(window, Qt.Key_Space)
        qt_app.processEvents()
        assert page.property("selectedAgent") == 1
        assert title.property("text") == "Meal planning"
        QTest.keyClick(window, Qt.Key_Return)
        assert page.property("selectedAgent") == 1

        assert demo.setLanguage("fr")
        qt_app.processEvents()
        assert title.property("text") == "Planification des repas"
        assert not window.grabWindow().isNull()
        assert not warnings, "\n".join(warnings)
    finally:
        window.close()
        engine.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
