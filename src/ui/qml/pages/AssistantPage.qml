import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: page
    objectName: "assistantPage"
    required property var store
    property var assistant: store.assistant
    property int dictationTarget: 0
    property int submittedTarget: 0
    property bool clearingRequest: false
    readonly property bool compact: height < 680
    signal planningRequested
    signal foodRequested
    signal pantryRequested
    signal groceriesRequested
    clip: true
    contentWidth: availableWidth

    ColumnLayout {
        width: page.availableWidth
        spacing: page.compact ? 12 : 18
        RowLayout {
            Layout.fillWidth: true
            spacing: page.availableWidth < 800 ? 12 : 18
            OverviewCard {
                objectName: "mealOverview"
                implicitHeight: page.compact ? 80 : 88
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                text: I18n.tr("text.planned_meals")
                iconName: "planning"
                count: page.store.meals.length
                onClicked: page.planningRequested()
            }
            OverviewCard {
                objectName: "pantryOverview"
                implicitHeight: page.compact ? 80 : 88
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                text: I18n.tr("text.foods_in_your_pantry_2")
                iconName: "pantry"
                count: page.store.pantry.length
                onClicked: page.pantryRequested()
            }
            OverviewCard {
                objectName: "groceryOverview"
                implicitHeight: page.compact ? 80 : 88
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                text: I18n.tr("text.items_to_buy")
                iconName: "groceries"
                count: page.store.groceries.filter(item => !item.available && !item.checked).length
                onClicked: page.groceriesRequested()
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            Layout.topMargin: 6
            spacing: 6
            Heading {
                text: I18n.tr("text.what_would_you_like_to_organize")
                font.pixelSize: page.compact ? 24 : 28
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                elide: Text.ElideNone
            }
            Caption {
                text: I18n.tr("text.describe_a_meal_to_cook_a_purchase_to_add")
                Layout.fillWidth: true
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6
            readonly property string householdFoods: [page.store.settings.foods_to_avoid].concat(page.store.settings.members.map(member => member.foods_to_avoid)).filter(value => value.length > 0).join(", ")
            visible: householdFoods.length > 0 || page.store.settings.guest_groups.length > 0
            Caption {
                Layout.fillWidth: true
                color: Theme.accent
                text: I18n.tr("text.recipes_automatically_adapt_to_each_meal_s_preferences")
            }
            Caption {
                objectName: "householdDietarySummary"
                Layout.fillWidth: true
                visible: parent.householdFoods.length > 0
                text: I18n.tr("text.every_meal_foods_to_avoid") + parent.householdFoods
            }
            Repeater {
                model: page.store.settings.guest_groups
                delegate: Caption {
                    required property var modelData
                    required property int index
                    objectName: "guestDietarySummary-" + index
                    Layout.fillWidth: true
                    text: (modelData.name || I18n.tr("text.guests_2")) + " · " + modelData.meals.map(i => I18n.tr("prefix.meal") + (i + 1)).join(", ") + " · " + modelData.members.map(member => (member.name || I18n.tr("text.guests_2")) + (member.foods_to_avoid ? " : " + member.foods_to_avoid : "")).join(" ; ")
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: page.availableWidth < 800 ? 12 : 18
            Repeater {
                id: fields
                model: [
                    { label: "text.my_meals", icon: "planning", name: "planningRequest", description: "text.from_ideas_to_recipes", example: "text.i_want_to_make_tiramisu_for_six_people", prompt: "text.i_want_to_make_tiramisu_for_six_people", exampleIndex: 0, context: "" },
                    { label: "text.my_pantry", icon: "pantry", name: "pantryRequest", description: "text.what_you_already_have", example: "text.i_have_500_g_of_rice", prompt: "text.i_have_500_g_of_rice", exampleIndex: 2, context: "text.available_pantry_food" },
                    { label: "text.my_groceries", icon: "groceries", name: "groceryRequest", description: "text.remember_every_essential", example: "text.add_three_potatoes_to_buy_next_week", prompt: "text.add_three_potatoes_to_buy_next_week", exampleIndex: 1, context: "text.groceries_to_buy" }
                ]
                delegate: Panel {
                    id: card
                    required property var modelData
                    required property int index
                    property alias field: request
                    readonly property color tint: index === 0 ? Theme.accent : index === 1 ? Theme.secondary : "#e4c89c"
                    objectName: modelData.name + "Card"
                    Layout.fillWidth: true
                    Layout.preferredWidth: 1
                    implicitHeight: page.compact ? 332 : 382
                    border.color: request.activeFocus ? card.tint : Theme.border
                    Rectangle {
                        anchors.top: parent.top
                        anchors.topMargin: 1
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: parent.width - 40
                        height: 2
                        color: card.tint
                        opacity: 0.8
                    }
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: page.availableWidth < 800 ? 14 : 20
                        spacing: 12
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 10
                            Rectangle {
                                implicitWidth: 34
                                implicitHeight: 34
                                radius: 11
                                color: Theme.raised
                                AppIcon {
                                    anchors.centerIn: parent
                                    name: card.modelData.icon
                                    color: card.tint
                                    width: 20
                                    height: 20
                                }
                            }
                            Heading {
                                text: I18n.tr(card.modelData.label)
                                Layout.fillWidth: true
                                font.pixelSize: page.availableWidth < 800 ? 16 : 18
                            }
                        }
                        Caption {
                            text: I18n.tr(card.modelData.description)
                            Layout.fillWidth: true
                            font.pixelSize: 12
                        }
                        Rectangle {
                            id: editor
                            visible: card.index !== 1
                            objectName: card.modelData.name + "Editor"
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            radius: 12
                            color: Theme.background
                            border.color: request.activeFocus ? card.tint : Theme.border
                            Behavior on border.color {
                                ColorAnimation { duration: Theme.motionDuration }
                            }
                            ColumnLayout {
                                anchors.fill: parent
                                anchors.margins: 6
                                spacing: 0
                                ScrollView {
                                    Layout.fillWidth: true
                                    Layout.fillHeight: true
                                    clip: true
                                    contentWidth: availableWidth
                                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                                    TextArea {
                                        id: request
                                        objectName: card.modelData.name
                                        enabled: !page.assistant.busy && !page.assistant.recording
                                        Accessible.description: I18n.tr("text.example") + I18n.tr(card.modelData.example)
                                        Accessible.name: I18n.tr(card.modelData.label)
                                        wrapMode: TextEdit.WordWrap
                                        color: Theme.text
                                        placeholderTextColor: Theme.muted
                                        font.pixelSize: 13
                                        selectionColor: Theme.accent
                                        selectedTextColor: Theme.accentDark
                                        selectByMouse: true
                                        padding: 10
                                        background: Item {}
                                        Caption {
                                            x: request.leftPadding
                                            y: request.topPadding
                                            width: request.width - request.leftPadding - request.rightPadding
                                            text: I18n.tr("text.example") + I18n.tr(card.modelData.example)
                                            font: request.font
                                            opacity: 0.6
                                            visible: request.text.length === 0
                                        }
                                        onTextChanged: if (!page.clearingRequest) page.assistant.discard()
                                    }
                                }
                                RowLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    ActionButton {
                                        id: microphone
                                        objectName: card.index === 0 ? "dictationButton" : card.modelData.name + "DictationButton"
                                        readonly property bool recordingHere: page.assistant.recording && page.dictationTarget === card.index
                                        text: recordingHere ? I18n.tr("text.stop_and_transcribe") : I18n.tr("text.dictate_my_request")
                                        Accessible.description: I18n.tr(card.modelData.label)
                                        quiet: true
                                        implicitWidth: 40
                                        implicitHeight: 36
                                        padding: 8
                                        ToolTip.visible: hovered || activeFocus
                                        ToolTip.text: text
                                        contentItem: Item {
                                            AppIcon {
                                                anchors.centerIn: parent
                                                width: 20
                                                height: 20
                                                name: "microphone"
                                                visible: !microphone.recordingHere
                                                color: microphone.enabled ? card.tint : Theme.border
                                            }
                                            Rectangle {
                                                anchors.centerIn: parent
                                                width: 12
                                                height: 12
                                                radius: 3
                                                visible: microphone.recordingHere
                                                color: Theme.danger
                                            }
                                        }
                                        background: Rectangle {
                                            radius: 18
                                            color: microphone.recordingHere || microphone.hovered ? Theme.raised : "transparent"
                                            border.color: microphone.activeFocus ? card.tint : "transparent"
                                        }
                                        enabled: !page.assistant.busy && (!page.assistant.recording || page.dictationTarget === card.index)
                                        onClicked: {
                                            if (page.assistant.recording) page.assistant.stopDictation();
                                            else { page.dictationTarget = card.index; page.assistant.startDictation(); }
                                        }
                                    }
                                    ActionButton {
                                        visible: microphone.recordingHere
                                        text: I18n.tr("text.cancel")
                                        quiet: true
                                        implicitWidth: contentItem.implicitWidth + 8
                                        implicitHeight: 36
                                        padding: 4
                                        font.pixelSize: 11
                                        onClicked: page.assistant.cancelDictation()
                                    }
                                    Item { Layout.fillWidth: true }
                                    ActionButton {
                                        id: send
                                        visible: !microphone.recordingHere
                                        objectName: card.index === 0 ? "generatePlanButton" : card.modelData.name + "SendButton"
                                        text: I18n.tr("text.send")
                                        Accessible.name: I18n.tr("text.send_request") + " — " + I18n.tr(card.modelData.label)
                                        primary: true
                                        implicitHeight: 36
                                        implicitWidth: 100
                                        padding: 10
                                        enabled: request.text.trim().length > 0 && !page.assistant.busy && !page.assistant.recording
                                        background: Rectangle {
                                            radius: 18
                                            color: !send.enabled ? Theme.surface : send.hovered ? Qt.lighter(card.tint, 1.1) : card.tint
                                            border.color: send.activeFocus ? Theme.text : "transparent"
                                        }
                                        contentItem: Item {
                                            RowLayout {
                                                anchors.centerIn: parent
                                                spacing: 8
                                                Text {
                                                    text: send.text
                                                    color: send.enabled ? Theme.accentDark : Theme.muted
                                                    font.pixelSize: 12
                                                    font.weight: Font.DemiBold
                                                    verticalAlignment: Text.AlignVCenter
                                                }
                                                Text {
                                                    text: "↑"
                                                    color: send.enabled ? Theme.accentDark : Theme.muted
                                                    font.pixelSize: 17
                                                    verticalAlignment: Text.AlignVCenter
                                                }
                                            }
                                        }
                                        onClicked: { page.submittedTarget = card.index; page.assistant.plan(I18n.tr(card.modelData.context) + request.text); }
                                    }
                                }
                            }
                        }
                        ColumnLayout {
                            visible: card.index === 1
                            Layout.fillWidth: true
                            Layout.fillHeight: true
                            spacing: 12
                            Caption {
                                Layout.fillWidth: true
                                text: I18n.tr("text.enter_quantities_when_adding_food_total_weight_or_number")
                            }
                            Caption {
                                Layout.fillWidth: true
                                text: I18n.tr("text.example_2_tubs_of_mascarpone_at_250_g_each")
                            }
                            ActionButton {
                                objectName: card.index === 1 ? "addPantryFoodButton" : ""
                                Layout.fillWidth: true
                                text: I18n.tr("text.add_food_2")
                                primary: true
                                onClicked: page.foodRequested()
                            }
                            Item { Layout.fillHeight: true }
                        }
                        ActionButton {
                            id: example
                            visible: card.index !== 1
                            objectName: "requestExample" + card.modelData.exampleIndex
                            text: I18n.tr("text.insert_an_example")
                            quiet: true
                            implicitHeight: 28
                            font.pixelSize: 11
                            padding: 4
                            Accessible.description: I18n.tr(card.modelData.prompt)
                            ToolTip.visible: hovered || activeFocus
                            ToolTip.text: I18n.tr(card.modelData.prompt)
                            contentItem: Text {
                                text: example.text + "  ↗"
                                color: card.tint
                                font: example.font
                                verticalAlignment: Text.AlignVCenter
                            }
                            enabled: !page.assistant.busy && !page.assistant.recording
                            onClicked: {
                                request.text = I18n.tr(card.modelData.prompt);
                                request.forceActiveFocus();
                                request.cursorPosition = request.length;
                            }
                        }
                    }
                }
            }
        }
        Caption {
            text: page.assistant.recording ? I18n.tr("text.recording_5_minutes_maximum") : page.assistant.busy ? page.assistant.status : I18n.tr("text.local_dictation_with_parakeet_text_and_context_are_sent")
            Layout.fillWidth: true
            font.pixelSize: 11
            Accessible.role: Accessible.StaticText
        }
        Panel {
            objectName: "assistantProgressPanel"
            visible: page.assistant.status.length > 0 || page.assistant.steps.length > 0
            Layout.fillWidth: true
            implicitHeight: progressContent.implicitHeight + 32
            ColumnLayout {
                id: progressContent
                anchors.fill: parent
                anchors.margins: 16
                spacing: 10
                RowLayout {
                    visible: page.assistant.status.length > 0
                    Layout.fillWidth: true
                    BusyIndicator {
                        running: page.assistant.busy
                        visible: running
                        Layout.preferredWidth: 28
                        Layout.preferredHeight: 28
                    }
                    Caption {
                        objectName: "assistantStatus"
                        text: page.assistant.status
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                    }
                    Caption {
                        visible: page.assistant.busy
                        text: elapsed.seconds + I18n.tr("text.s_elapsed")
                    }
                }
                Repeater {
                    model: page.assistant.steps
                    delegate: Caption {
                        required property string modelData
                        required property int index
                        text: (index + 1) + ". " + modelData
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        font.pixelSize: 12
                    }
                }
            }
        }
        Timer {
            id: elapsed
            property int seconds: 0
            interval: 1000
            repeat: true
            running: page.assistant.busy
            onRunningChanged: if (running) seconds = 0
            onTriggered: seconds += 1
        }
        Caption {
            objectName: "assistantError"
            text: page.assistant.error
            visible: text.length > 0
            color: Theme.danger
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            Accessible.role: Accessible.AlertMessage
        }
        Caption {
            objectName: "coordinatorReply"
            text: page.assistant.reply
            visible: text.length > 0
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
        }
        Caption {
            text: page.store.coordinatorError
            visible: text.length > 0
            color: Theme.danger
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
        }
        Repeater {
            model: page.assistant.completedActions
            delegate: Caption {
                required property string modelData
                text: "✓ " + modelData
                color: Theme.accent
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }
        }

    }
    Connections {
        target: page.assistant
        function onTranscribed(text) {
            const field = fields.itemAt(page.dictationTarget).field;
            field.text = field.text.length ? field.text + " " + text : text;
        }
        function onApplied() {
            page.clearingRequest = true;
            fields.itemAt(page.submittedTarget).field.text = "";
            page.clearingRequest = false;
        }
    }
}
