import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: page
    objectName: "agentInteractionsPage"
    contentWidth: availableWidth
    clip: true
    property int selectedAgent: 0
    readonly property color incomingColor: "#a5c8e8"
    readonly property var workflowLinks: [
        {from: "user", to: "coordinator", fromAgent: -1, toAgent: 0, label: I18n.tr("Demande")},
        {from: "coordinator", to: "planning", fromAgent: 0, toAgent: 1, label: I18n.tr("Repas")},
        {from: "coordinator", to: "preferences", fromAgent: 0, toAgent: 2, label: I18n.tr("Préférences")},
        {from: "coordinator", to: "groceries", fromAgent: 0, toAgent: 3, label: I18n.tr("Repas retenus")},
        {from: "groceries", to: "verification", fromAgent: 3, toAgent: 4, label: I18n.tr("Liste")}
    ]
    readonly property var agents: [
        {
            title: I18n.tr("Orchestrateur"), kind: "coordinator", tint: "#b7d99a",
            role: I18n.tr("Orchestre la planification des repas, les préférences alimentaires et la liste de courses."),
            input: I18n.tr("Votre demande, la réserve, le foyer, les invités et les préférences."),
            output: I18n.tr("Des consignes pour les agents de repas, de préférences et de courses.")
        },
        {
            title: I18n.tr("Planification des repas"), kind: "planning", tint: "#a5c8e8",
            role: I18n.tr("Compose les repas en tenant compte des ingrédients, de la période et des convives."),
            input: I18n.tr("Les consignes de l’orchestrateur, les ingrédients et le nombre de convives."),
            output: I18n.tr("Un planning et les recettes proposées pour chaque repas.")
        },
        {
            title: I18n.tr("Préférences alimentaires"), kind: "preferences", tint: "#d2b8e8",
            role: I18n.tr("Contrôle les recettes pour respecter les préférences et les aliments exclus du foyer."),
            input: I18n.tr("Les recettes proposées, le régime et les aliments exclus."),
            output: I18n.tr("Des repas compatibles avec les préférences du foyer.")
        },
        {
            title: I18n.tr("Liste de courses"), kind: "groceries", tint: "#e5c397",
            role: I18n.tr("Calcule les besoins et distingue les ingrédients en réserve de ceux à acheter."),
            input: I18n.tr("Les repas retenus, les quantités en réserve et les portions."),
            output: I18n.tr("Une liste de courses avec les quantités manquantes.")
        },
        {
            title: I18n.tr("Vérification des courses"), kind: "verification", tint: "#94d1c6",
            role: I18n.tr("Vérifie la liste de courses produite et signale les manques ou incohérences."),
            input: I18n.tr("La liste de courses et les quantités retenues par l’agent des courses."),
            output: I18n.tr("Les éventuels manques et incohérences détectés.")
        }
    ]
    readonly property var selected: agents[selectedAgent]

    ColumnLayout {
        width: page.availableWidth
        spacing: 18
        RowLayout {
            Layout.fillWidth: true
            Heading {
                text: I18n.tr("Circuit des agents")
                Layout.fillWidth: true
            }
            Rectangle {
                implicitWidth: architectureLabel.implicitWidth + 24
                implicitHeight: 30
                radius: 15
                color: Theme.raised
                Text {
                    id: architectureLabel
                    anchors.centerIn: parent
                    text: I18n.tr("Agents connectés")
                    font.pixelSize: 11
                    color: Theme.muted
                }
            }
        }
        Caption {
            text: I18n.tr("Sélectionnez un agent pour explorer son rôle et ses échanges.")
            Layout.fillWidth: true
        }
        Panel {
            Layout.fillWidth: true
            implicitHeight: graph.height + 50
            color: "#252f34"
            Item {
                id: graph
                objectName: "agentGraph"
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                height: page.availableHeight < 700 ? 440 : 520
                readonly property real nodeWidth: Math.min(176, Math.max(124, (width - 90) / 4))
                // Four columns fit the user, orchestrator, three delegated
                // tasks, and the grocery-only verification step.
                function center(id) {
                    const left = nodeWidth / 2 + 8;
                    const step = (width - 2 * left) / 3;
                    const middle = height / 2;
                    if (id === "user") return {x: left, y: middle};
                    if (id === "coordinator") return {x: left + step, y: middle};
                    if (id === "planning") return {x: left + 2 * step, y: height * 0.18};
                    if (id === "preferences") return {x: left + 2 * step, y: middle};
                    if (id === "groceries") return {x: left + 2 * step, y: height * 0.82};
                    return {x: left + 3 * step, y: height * 0.82};
                }
                function edge(link) {
                    const from = center(link.from);
                    const to = center(link.to);
                    const dx = to.x - from.x;
                    const dy = to.y - from.y;
                    // Intersect the node rectangles so arrowheads end at the
                    // card borders at every supported window width.
                    const scale = Math.min(
                        dx === 0 ? Infinity : (nodeWidth / 2) / Math.abs(dx),
                        dy === 0 ? Infinity : 54 / Math.abs(dy)
                    );
                    const middle = {x: (from.x + to.x) / 2, y: (from.y + to.y) / 2};
                    const label = dy === 0
                        ? {x: middle.x, y: middle.y - 66}
                        : {x: to.x, y: middle.y};
                    return {
                        start: {x: from.x + dx * scale, y: from.y + dy * scale},
                        end: {x: to.x - dx * scale, y: to.y - dy * scale},
                        middle: middle,
                        label: label
                    };
                }
                function edgeColor(link) {
                    return link.fromAgent === page.selectedAgent ? Theme.accent
                        : link.toAgent === page.selectedAgent ? page.incomingColor : "#72848b";
                }
                Canvas {
                    id: connections
                    objectName: "agentConnections"
                    property var linkPairs: page.workflowLinks.map(link => link.from + "->" + link.to)
                    anchors.fill: parent
                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                    onPaint: {
                        const ctx = getContext("2d");
                        ctx.reset();
                        for (const relation of page.workflowLinks) {
                            const link = graph.edge(relation);
                            const angle = Math.atan2(link.end.y - link.start.y, link.end.x - link.start.x);
                            ctx.strokeStyle = graph.edgeColor(relation);
                            ctx.fillStyle = graph.edgeColor(relation);
                            ctx.lineWidth = 2;
                            ctx.beginPath();
                            ctx.moveTo(link.start.x, link.start.y);
                            ctx.lineTo(link.end.x, link.end.y);
                            ctx.stroke();
                            ctx.beginPath();
                            ctx.moveTo(link.end.x, link.end.y);
                            ctx.lineTo(link.end.x - 10 * Math.cos(angle - 0.5), link.end.y - 10 * Math.sin(angle - 0.5));
                            ctx.lineTo(link.end.x - 10 * Math.cos(angle + 0.5), link.end.y - 10 * Math.sin(angle + 0.5));
                            ctx.closePath(); ctx.fill();
                        }
                    }
                    Connections {
                        target: page
                        function onSelectedAgentChanged() { connections.requestPaint(); }
                    }
                }
                Rectangle {
                    id: userNode
                    objectName: "userNode"
                    x: graph.center("user").x - width / 2
                    y: graph.center("user").y - height / 2
                    width: graph.nodeWidth
                    height: 108
                    radius: 16
                    color: Theme.surface
                    border.color: Theme.border
                    Accessible.name: I18n.tr("Utilisateur")
                    Accessible.description: I18n.tr("Envoie ses données de planification à l’orchestrateur.")
                    Accessible.role: Accessible.StaticText
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 8
                        RowLayout {
                            Layout.fillWidth: true
                            Rectangle {
                                width: 36
                                height: 36
                                radius: 10
                                color: Qt.rgba(Theme.accent.r, Theme.accent.g, Theme.accent.b, 0.12)
                                AgentIcon {
                                    anchors.centerIn: parent
                                    width: 27
                                    height: 27
                                    kind: "user"
                                    ink: Theme.accent
                                }
                            }
                        }
                        Text {
                            Layout.fillWidth: true
                            text: I18n.tr("Utilisateur")
                            color: Theme.text
                            font.pixelSize: 13
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                            Layout.fillHeight: true
                            verticalAlignment: Text.AlignVCenter
                        }
                    }
                }
                Repeater {
                    model: page.workflowLinks
                    delegate: Rectangle {
                        required property var modelData
                        required property int index
                        readonly property var points: graph.edge(modelData)
                        objectName: "linkLabel" + modelData.from + "To" + modelData.to
                        x: points.label.x - width / 2
                        y: points.label.y - height / 2
                        width: linkText.implicitWidth + 14
                        height: 24
                        radius: 12
                        color: "#252f34"
                        Text {
                            id: linkText
                            anchors.centerIn: parent
                            text: modelData.label
                            font.pixelSize: 10
                            color: graph.edgeColor(modelData)
                        }
                    }
                }
                Repeater {
                    model: page.agents
                    delegate: AgentNode {
                        required property var modelData
                        required property int index
                        objectName: "agentNode" + index
                        readonly property var nodeIds: ["coordinator", "planning", "preferences", "groceries", "verification"]
                        nodeWidth: graph.nodeWidth
                        x: graph.center(nodeIds[index]).x - width / 2
                        y: graph.center(nodeIds[index]).y - height / 2
                        title: modelData.title
                        kind: modelData.kind
                        step: index + 1
                        tint: modelData.tint
                        selected: page.selectedAgent === index
                        onClicked: page.selectedAgent = index
                    }
                }
            }
            RowLayout {
                anchors.top: graph.bottom
                anchors.bottom: parent.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 10
                Rectangle { width: 22; height: 2; color: page.incomingColor }
                Caption { text: I18n.tr("Entrée de l’agent sélectionné"); font.pixelSize: 11 }
                Rectangle { width: 22; height: 2; color: Theme.accent; Layout.leftMargin: 12 }
                Caption { text: I18n.tr("Sortie de l’agent sélectionné"); font.pixelSize: 11 }
            }
        }
        Panel {
            Layout.fillWidth: true
            implicitHeight: details.implicitHeight + 40
            ColumnLayout {
                id: details
                anchors.fill: parent
                anchors.margins: 20
                spacing: 14
                RowLayout {
                    spacing: 12
                    AgentIcon { kind: page.selected.kind; ink: page.selected.tint }
                    Heading {
                        objectName: "selectedAgentTitle"
                        text: page.selected.title
                        font.pixelSize: 18
                        Layout.fillWidth: true
                    }
                    Caption { text: "0" + (page.selectedAgent + 1) + " / 05" }
                }
                Caption {
                    objectName: "selectedAgentRole"
                    text: page.selected.role
                    Layout.fillWidth: true
                    color: Theme.text
                }
                GridLayout {
                    Layout.fillWidth: true
                    columns: width < 600 ? 1 : 2
                    columnSpacing: 12
                    rowSpacing: 12
                        Repeater {
                        model: [
                            {label: I18n.tr("Reçoit"), body: page.selected.input, tint: page.incomingColor},
                            {label: I18n.tr("Résultat"), body: page.selected.output, tint: Theme.accent}
                        ]
                        delegate: Rectangle {
                            required property var modelData
                            Layout.fillWidth: true
                            Layout.preferredWidth: 1
                            implicitHeight: exchange.implicitHeight + 28
                            radius: 10
                            color: Theme.background
                            ColumnLayout {
                                id: exchange
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 8
                                Caption {
                                    text: modelData.label
                                    color: modelData.tint
                                    font.weight: Font.DemiBold
                                    Layout.fillWidth: true
                                }
                                Caption {
                                    text: modelData.body
                                    Layout.fillWidth: true
                                }
                            }
                        }
                    }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.bottomMargin: 4
            spacing: 10
            Rectangle {
                width: 8
                height: 8
                radius: 4
                color: Theme.muted
            }
            Caption {
                objectName: "agentInteractionsStatus"
                text: I18n.tr("Orchestrateur, planification, préférences et courses actifs. La vérification des courses reste à implémenter.")
                Layout.fillWidth: true
            }
        }
    }
}
