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
                text: I18n.tr("repas planifiés")
                iconName: "planning"
                count: page.store.meals.length
                onClicked: page.planningRequested()
            }
            OverviewCard {
                objectName: "pantryOverview"
                implicitHeight: page.compact ? 80 : 88
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                text: I18n.tr("aliments en réserve")
                iconName: "pantry"
                count: page.store.pantry.length
                onClicked: page.pantryRequested()
            }
            OverviewCard {
                objectName: "groceryOverview"
                implicitHeight: page.compact ? 80 : 88
                Layout.fillWidth: true
                Layout.preferredWidth: 1
                text: I18n.tr("articles à acheter")
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
                text: I18n.tr("Que souhaitez-vous organiser ?")
                font.pixelSize: page.compact ? 24 : 28
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                elide: Text.ElideNone
            }
            Caption {
                text: I18n.tr("Décrivez un repas à préparer, un achat à ajouter ou les aliments disponibles.")
                Layout.fillWidth: true
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: page.availableWidth < 800 ? 12 : 18
            Repeater {
                id: fields
                model: [
                    { label: "Mes repas", icon: "planning", name: "planningRequest", description: "Des envies aux recettes", example: "Je veux faire un tiramisu pour six personnes.", prompt: "Je veux faire un tiramisu pour six personnes.", exampleIndex: 0, context: "" },
                    { label: "Ma réserve", icon: "pantry", name: "pantryRequest", description: "Ce que vous avez déjà", example: "J’ai 500 g de riz.", prompt: "J’ai 500 g de riz.", exampleIndex: 2, context: "Aliments disponibles en réserve : " },
                    { label: "Mes courses", icon: "groceries", name: "groceryRequest", description: "Pour ne rien oublier", example: "Ajoute trois pommes de terre à acheter la semaine prochaine.", prompt: "Ajoute trois pommes de terre à acheter la semaine prochaine.", exampleIndex: 1, context: "Courses à acheter : " }
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
                                        Accessible.description: I18n.tr("Exemple : ") + I18n.tr(card.modelData.example)
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
                                            text: I18n.tr("Exemple : ") + I18n.tr(card.modelData.example)
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
                                        text: recordingHere ? I18n.tr("Arrêter et transcrire") : I18n.tr("Dicter ma demande")
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
                                        text: I18n.tr("Annuler")
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
                                        text: I18n.tr("Envoyer")
                                        Accessible.name: I18n.tr("Envoyer la demande") + " — " + I18n.tr(card.modelData.label)
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
                        ActionButton {
                            id: example
                            objectName: "requestExample" + card.modelData.exampleIndex
                            text: I18n.tr("Insérer un exemple")
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
            text: page.assistant.recording ? I18n.tr("Enregistrement en cours — 5 minutes maximum.") : page.assistant.busy ? page.assistant.status : I18n.tr("Dictée locale avec Parakeet. Le texte et le contexte sont envoyés à GLM pour interprétation.")
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
                        text: elapsed.seconds + I18n.tr(" s écoulées")
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
