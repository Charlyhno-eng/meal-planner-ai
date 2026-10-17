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
    property bool motionEnabled: true
    readonly property color incomingColor: "#a5c8e8"
    readonly property var workflowLinks: [
        {from: "user", to: "coordinator", fromAgent: -1, toAgent: 0, label: I18n.tr("text.request")},
        {from: "coordinator", to: "planning", fromAgent: 0, toAgent: 1, label: I18n.tr("text.meals_2")},
        {from: "coordinator", to: "preferences", fromAgent: 0, toAgent: 2, label: I18n.tr("text.preferences")},
        {from: "coordinator", to: "groceries", fromAgent: 0, toAgent: 3, label: I18n.tr("text.selected_meals")},
        {from: "groceries", to: "verification", fromAgent: 3, toAgent: 4, label: I18n.tr("text.list")},
        {from: "pantry", to: "planning", fromAgent: 5, toAgent: 1, label: I18n.tr("text.stock")},
        {from: "pantry", to: "groceries", fromAgent: 5, toAgent: 3, label: I18n.tr("text.pantry_quantities")},
        {from: "planning", to: "groceries", fromAgent: 1, toAgent: 3, label: I18n.tr("text.required_ingredients")},
        {from: "groceries", to: "planning", fromAgent: 3, toAgent: 1, label: I18n.tr("text.stock_purchases")}
    ]
    readonly property var agents: [
        {
            title: I18n.tr("text.orchestrator"), kind: "coordinator", tint: "#b7d99a",
            role: I18n.tr("text.coordinates_meal_planning_dietary_preferences_and_grocery_list_preparation"),
            input: I18n.tr("text.your_request_pantry_household_guests_and_preferences"),
            output: I18n.tr("text.instructions_for_the_meal_preferences_and_grocery_agents")
        },
        {
            title: I18n.tr("text.meal_planning"), kind: "planning", tint: "#a5c8e8",
            role: I18n.tr("text.plans_meals_based_on_ingredients_the_planning_period_and"),
            input: I18n.tr("text.orchestrator_instructions_pantry_stock_and_the_number_of_diners"),
            output: I18n.tr("text.recipes_and_their_requirements_sent_to_groceries_ingredient_coverage")
        },
        {
            title: I18n.tr("text.food_preferences"), kind: "preferences", tint: "#d2b8e8",
            role: I18n.tr("text.checks_recipes_against_household_preferences_and_excluded_foods"),
            input: I18n.tr("text.proposed_recipes_dietary_preferences_and_excluded_foods"),
            output: I18n.tr("text.meals_compatible_with_household_preferences")
        },
        {
            title: I18n.tr("text.grocery_list"), kind: "groceries", tint: "#e5c397",
            role: I18n.tr("text.calculates_requirements_and_separates_pantry_ingredients_from_those_to"),
            input: I18n.tr("text.selected_meals_pantry_quantities_and_servings"),
            output: I18n.tr("text.purchase_quantities_and_ingredient_coverage_returned_to_meals")
        },
        {
            title: I18n.tr("text.grocery_verification"), kind: "verification", tint: "#94d1c6",
            role: I18n.tr("text.checks_the_grocery_list_and_reports_missing_items_or"),
            input: I18n.tr("text.the_grocery_list_and_quantities_prepared_by_the_grocery"),
            output: I18n.tr("text.any_missing_items_or_inconsistencies_found")
        },
        {
            title: I18n.tr("text.pantry"), kind: "pantry", tint: "#d5c49f",
            role: I18n.tr("text.local_service_maintains_stock_and_supplies_available_quantities_to"),
            input: I18n.tr("text.foods_and_quantities_entered_in_the_pantry"),
            output: I18n.tr("text.available_stock_for_preparing_recipes_and_calculating_missing_purchases")
        }
    ]
    readonly property var selected: agents[selectedAgent]

    ColumnLayout {
        width: page.availableWidth
        spacing: 18
        RowLayout {
            Layout.fillWidth: true
            Heading {
                text: I18n.tr("text.agent_workflow")
                Layout.fillWidth: true
            }
            ActionButton {
                objectName: "agentAnimationToggle"
                text: page.motionEnabled ? I18n.tr("text.pause") : I18n.tr("text.animate")
                quiet: true
                implicitHeight: 30
                font.pixelSize: 11
                Accessible.name: page.motionEnabled ? I18n.tr("text.pause_animations") : I18n.tr("text.resume_animations")
                onClicked: page.motionEnabled = !page.motionEnabled
            }
            Rectangle {
                implicitWidth: architectureLabel.implicitWidth + 24
                implicitHeight: 30
                radius: 15
                color: Theme.raised
                Text {
                    id: architectureLabel
                    anchors.centerIn: parent
                    text: I18n.tr("text.illustrated_exchanges")
                    font.pixelSize: 11
                    color: Theme.muted
                }
            }
        }
        Caption {
            text: I18n.tr("text.select_an_agent_to_explore_its_role_and_exchanges")
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
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                height: page.availableHeight < 700 ? 440 : 520
                readonly property real nodeWidth: Math.min(184, (width - 80) / 4)
                readonly property var routes: page.workflowLinks.map(link => edge(link))
                // A planar layout: each exchange has its own port and corridor.
                function center(id) {
                    const top = 64;
                    const middle = height / 2;
                    const bottom = height - 64;
                    if (id === "user") return {x: width * 0.13, y: top};
                    if (id === "coordinator") return {x: width * 0.45, y: top};
                    if (id === "preferences") return {x: width * 0.83, y: top};
                    if (id === "planning") return {x: width * 0.22, y: middle};
                    if (id === "groceries") return {x: width * 0.68, y: middle};
                    if (id === "pantry") return {x: width * 0.45, y: bottom};
                    return {x: width * 0.83, y: bottom};
                }
                function rounded(points) {
                    const result = [points[0]];
                    for (let i = 1; i < points.length - 1; i++) {
                        const a = points[i - 1], b = points[i], c = points[i + 1];
                        const before = Math.hypot(b.x - a.x, b.y - a.y);
                        const after = Math.hypot(c.x - b.x, c.y - b.y);
                        const radius = Math.min(10, before / 2, after / 2);
                        const entry = {x: b.x + (a.x - b.x) * radius / before, y: b.y + (a.y - b.y) * radius / before};
                        const exit = {x: b.x + (c.x - b.x) * radius / after, y: b.y + (c.y - b.y) * radius / after};
                        result.push(entry);
                        for (let j = 1; j <= 8; j++) {
                            const t = j / 8, u = 1 - t;
                            result.push({x: u * u * entry.x + 2 * u * t * b.x + t * t * exit.x,
                                         y: u * u * entry.y + 2 * u * t * b.y + t * t * exit.y});
                        }
                    }
                    result.push(points[points.length - 1]);
                    return result;
                }
                function edge(link) {
                    const from = center(link.from), to = center(link.to);
                    const half = nodeWidth / 2;
                    let points, label;
                    if (link.from === "user" || link.to === "preferences") {
                        points = [{x: from.x + half, y: from.y}, {x: to.x - half, y: to.y}];
                        label = {x: (points[0].x + points[1].x) / 2, y: from.y};
                    } else if (link.from === "planning" || (link.from === "groceries" && link.to === "planning")) {
                        const forward = link.from === "planning";
                        const y = from.y + (forward ? -14 : 14);
                        points = [{x: from.x + (forward ? half : -half), y: y},
                                  {x: to.x + (forward ? -half : half), y: y}];
                        label = {x: (from.x + to.x) / 2, y: y + (forward ? -17 : 17)};
                    } else {
                        const upward = link.from === "pantry";
                        const direction = upward ? -1 : 1;
                        const port = link.to === "planning" ? -0.22 : 0.22;
                        const start = {x: from.x + nodeWidth * port, y: from.y + direction * 54};
                        const end = {x: to.x, y: to.y - direction * 54};
                        const lane = (start.y + end.y) / 2;
                        points = [start, {x: start.x, y: lane}, {x: end.x, y: lane}, end];
                        label = {x: (start.x + end.x) / 2, y: lane};
                    }
                    return {points: rounded(points), label: label};
                }
                function pointAt(points, progress) {
                    const lengths = [];
                    let total = 0;
                    for (let i = 1; i < points.length; i++) {
                        const length = Math.hypot(points[i].x - points[i - 1].x, points[i].y - points[i - 1].y);
                        lengths.push(length);
                        total += length;
                    }
                    let distance = progress * total;
                    for (let i = 0; i < lengths.length; i++) {
                        if (distance <= lengths[i]) {
                            const t = lengths[i] ? distance / lengths[i] : 0;
                            return {x: points[i].x + (points[i + 1].x - points[i].x) * t,
                                    y: points[i].y + (points[i + 1].y - points[i].y) * t};
                        }
                        distance -= lengths[i];
                    }
                    return points[points.length - 1];
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
                        ctx.lineCap = "round";
                        ctx.lineJoin = "round";
                        for (let i = 0; i < page.workflowLinks.length; i++) {
                            const relation = page.workflowLinks[i];
                            const points = graph.routes[i].points;
                            const end = points[points.length - 1];
                            const previous = points[points.length - 2];
                            const angle = Math.atan2(end.y - previous.y, end.x - previous.x);
                            ctx.strokeStyle = graph.edgeColor(relation);
                            ctx.fillStyle = graph.edgeColor(relation);
                            ctx.lineWidth = 2;
                            ctx.setLineDash(relation.to === "verification" ? [4, 5] : []);
                            ctx.beginPath();
                            ctx.moveTo(points[0].x, points[0].y);
                            for (let j = 1; j < points.length; j++) ctx.lineTo(points[j].x, points[j].y);
                            ctx.stroke();
                            ctx.setLineDash([]);
                            ctx.beginPath();
                            ctx.moveTo(end.x - 7 * Math.cos(angle - 0.5), end.y - 7 * Math.sin(angle - 0.5));
                            ctx.lineTo(end.x, end.y);
                            ctx.lineTo(end.x - 7 * Math.cos(angle + 0.5), end.y - 7 * Math.sin(angle + 0.5));
                            ctx.stroke();
                        }
                    }
                    Connections {
                        target: graph
                        function onRoutesChanged() { connections.requestPaint(); }
                    }
                    Connections {
                        target: page
                        function onSelectedAgentChanged() { connections.requestPaint(); }
                    }
                }
                Repeater {
                    model: page.workflowLinks
                    delegate: Rectangle {
                        id: pulse
                        required property var modelData
                        required property int index
                        objectName: "agentFlowPulse" + index
                        property real progress: 0
                        readonly property var position: graph.pointAt(graph.routes[index].points, progress)
                        readonly property bool active: page.visible
                        readonly property bool animating: active && page.motionEnabled
                        x: position.x - width / 2
                        y: position.y - height / 2
                        width: 7
                        height: 7
                        radius: 4
                        visible: active
                        color: graph.edgeColor(modelData)
                        Rectangle {
                            anchors.centerIn: parent
                            width: 15
                            height: 15
                            radius: 8
                            color: parent.color
                            opacity: 0.12
                        }
                        NumberAnimation on progress {
                            from: 0
                            to: 1
                            duration: 2600 + pulse.index * 130
                            loops: Animation.Infinite
                            running: pulse.active
                            paused: running && !page.motionEnabled
                        }
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
                    Accessible.name: I18n.tr("text.user")
                    Accessible.description: I18n.tr("text.sends_planning_details_to_the_orchestrator")
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
                            text: I18n.tr("text.user")
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
                        readonly property var points: graph.routes[index]
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
                        readonly property var nodeIds: ["coordinator", "planning", "preferences", "groceries", "verification", "pantry"]
                        nodeWidth: graph.nodeWidth
                        x: graph.center(nodeIds[index]).x - width / 2
                        y: graph.center(nodeIds[index]).y - height / 2
                        title: modelData.title
                        kind: modelData.kind
                        step: index + 1
                        planned: modelData.kind === "verification"
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
                Caption { text: I18n.tr("text.selected_agent_s_input"); font.pixelSize: 11 }
                Rectangle { width: 22; height: 2; color: Theme.accent; Layout.leftMargin: 12 }
                Caption { text: I18n.tr("text.selected_agent_s_output"); font.pixelSize: 11 }
            }
        }
        Caption {
            text: I18n.tr("text.illustrative_exchange_animation_without_live_activity_tracking")
            Layout.fillWidth: true
            font.pixelSize: 11
        }
        Panel {
            Layout.fillWidth: true
            implicitHeight: details.implicitHeight + 40
            ColumnLayout {
                id: details
                anchors.fill: parent
                anchors.margins: 20
                spacing: 14
                Connections {
                    target: page
                    function onSelectedAgentChanged() { detailReveal.restart(); }
                }
                NumberAnimation {
                    id: detailReveal
                    target: details
                    property: "opacity"
                    from: 0.55
                    to: 1
                    duration: Theme.motionDuration
                    easing.type: Easing.OutCubic
                }
                RowLayout {
                    spacing: 12
                    AgentIcon { kind: page.selected.kind; ink: page.selected.tint }
                    Heading {
                        objectName: "selectedAgentTitle"
                        text: page.selected.title
                        font.pixelSize: 18
                        Layout.fillWidth: true
                    }
                    Caption { text: page.selected.kind === "pantry" ? I18n.tr("text.local_service") : "0" + (page.selectedAgent + 1) + " / 05" }
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
                            {label: I18n.tr("text.receives"), body: page.selected.input, tint: page.incomingColor},
                            {label: I18n.tr("text.result"), body: page.selected.output, tint: Theme.accent}
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
                text: I18n.tr("text.orchestrator_meal_planning_preferences_and_groceries_are_active_grocery")
                Layout.fillWidth: true
            }
        }
    }
}
