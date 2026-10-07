"""Exercise the agent map's selection, keyboard access, and window resizing."""

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QLineF,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    Qt,
)
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from test_bootstrap import visual_child

from src.ui import app
from src.ui.demo import DemoState


@pytest.mark.parametrize("language", ["fr", "en"])
@pytest.mark.parametrize("size", [(960, 700), (1280, 880), (1440, 960)])
def test_agent_map_selection_keyboard_translation_and_geometry(
    qt_app, tmp_path, size, language
):
    demo = DemoState(config_path=tmp_path / "config.toml")
    demo.setLanguage(language)
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
            ("pantry", "planning"),
            ("pantry", "groceries"),
            ("planning", "groceries"),
            ("groceries", "planning"),
        ]
    ]
    title = window.findChild(QObject, "selectedAgentTitle")
    role = window.findChild(QObject, "selectedAgentRole")
    nodes = [visual_child(window.contentItem(), f"agentNode{i}") for i in range(6)]

    try:
        assert user is not None
        assert connections.property("linkPairs").toVariant() == [
            "user->coordinator",
            "coordinator->planning",
            "coordinator->preferences",
            "coordinator->groceries",
            "groceries->verification",
            "pantry->planning",
            "pantry->groceries",
            "planning->groceries",
            "groceries->planning",
        ]
        assert title.property("text") == demo.translate("Orchestrateur")

        # The full diagram remains visible at the minimum window size; nodes
        # neither overlap each other nor overflow the graph when resized.
        for width, height in [size, (960, 700), size]:
            window.setWidth(width)
            window.setHeight(height)
            QTest.qWait(30)
            bounds = []
            user_rect = user.mapRectToItem(graph, user.boundingRect())
            assert graph.boundingRect().contains(user_rect)
            assert user_rect.center().y() == pytest.approx(
                nodes[0].mapRectToItem(graph, nodes[0].boundingRect()).center().y()
            )
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
            label_bounds = []
            for label in link_labels:
                assert label is not None
                label_rect = label.mapRectToItem(graph, label.boundingRect())
                assert graph.boundingRect().contains(label_rect)
                overlaps_node = any(
                    label_rect.intersects(node_rect) for node_rect in bounds
                )
                assert not overlaps_node, f"{label.objectName()} overlaps a node"
                assert not any(label_rect.intersects(other) for other in label_bounds)
                label_bounds.append(label_rect)

            # Test the rendered paths, including bends: no exchange crosses
            # another exchange or passes through a card.
            routes = graph.property("routes").toVariant()
            segments = []
            for route in routes:
                points = [QPointF(p["x"], p["y"]) for p in route["points"]]
                lines = [QLineF(a, b) for a, b in zip(points, points[1:])]
                for line in lines:
                    for rect in bounds:
                        interior = rect.adjusted(0.1, 0.1, -0.1, -0.1)
                        assert not interior.contains(line.p1())
                        assert not interior.contains(line.p2())
                        for edge in (
                            QLineF(interior.topLeft(), interior.topRight()),
                            QLineF(interior.topRight(), interior.bottomRight()),
                            QLineF(interior.bottomRight(), interior.bottomLeft()),
                            QLineF(interior.bottomLeft(), interior.topLeft()),
                        ):
                            assert (
                                line.intersects(edge)[0] != QLineF.BoundedIntersection
                            )
                    for other in segments:
                        assert line.intersects(other)[0] != QLineF.BoundedIntersection
                segments.extend(lines)

        pulses = [
            visual_child(window.contentItem(), f"agentFlowPulse{i}") for i in range(9)
        ]
        for index, node in enumerate(nodes):
            position = node.mapToScene(QPoint(30, 30)).toPoint()
            QTest.mouseClick(window, Qt.LeftButton, Qt.NoModifier, position)
            qt_app.processEvents()
            assert page.property("selectedAgent") == index
            assert title.property("text") == node.property("title")
            assert role.property("text")
            assert all(p.property("animating") for p in pulses)
            assert all(p.isVisible() for p in pulses)
            assert [n.property("selected") for n in nodes] == [
                i == index for i in range(6)
            ]

        # Every connection advances, including planned verification and links
        # unrelated to the selection. Pause and page visibility control them all.
        before = [p.property("progress") for p in pulses]
        QTest.qWait(80)
        assert all(p.property("progress") != value for p, value in zip(pulses, before))
        toggle = visual_child(window.contentItem(), "agentAnimationToggle")
        QMetaObject.invokeMethod(toggle, "clicked")
        assert not page.property("motionEnabled")
        assert not any(p.property("animating") for p in pulses)
        before = [p.property("progress") for p in pulses]
        QTest.qWait(60)
        assert [p.property("progress") for p in pulses] == before
        window.setProperty("currentPage", 5)
        qt_app.processEvents()
        window.setProperty("currentPage", 6)
        qt_app.processEvents()
        assert not any(p.property("animating") for p in pulses)
        QMetaObject.invokeMethod(toggle, "clicked")
        assert all(p.property("animating") for p in pulses)
        window.setProperty("currentPage", 5)
        qt_app.processEvents()
        assert not any(p.property("animating") for p in pulses)
        window.setProperty("currentPage", 6)
        qt_app.processEvents()
        assert all(p.property("animating") for p in pulses)
        assert nodes[4].property("planned")

        # Switching language updates the selected node and inspector in place.
        assert demo.setLanguage("en")
        qt_app.processEvents()
        assert page.property("selectedAgent") == 5
        assert title.property("text") == "Pantry"
        assert nodes[5].property("kind") == "pantry"
        assert role.property("text").startswith("Local service: maintains stock")
        status = window.findChild(QObject, "agentInteractionsStatus")
        assert status.property("text").startswith(
            "Orchestrator, meal planning, preferences and groceries are active."
        )

        nodes = [visual_child(window.contentItem(), f"agentNode{i}") for i in range(6)]
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
