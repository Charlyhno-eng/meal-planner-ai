import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: page
    objectName: "assistantPage"
    required property var store
    property var assistant: store.assistant
    signal planningRequested
    signal configureRequested
    clip: true
    contentWidth: availableWidth

    ColumnLayout {
        width: page.availableWidth
        spacing: 18
        Heading {
            text: I18n.tr("Que souhaitez-vous organiser ?")
            font.pixelSize: 24
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
        }
        Caption {
            text: I18n.tr("Décrivez un repas à préparer, un achat à ajouter ou les aliments disponibles.")
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
        }
        Caption {
            text: I18n.tr("Une demande valide ajoute directement vos repas, leurs recettes et les courses nécessaires.")
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
        }
        TextArea {
            id: request
            objectName: "planningRequest"
            Layout.fillWidth: true
            Layout.preferredHeight: 150
            enabled: !page.assistant.busy && !page.assistant.recording
            placeholderText: I18n.tr("Ex. Je veux faire un tiramisu pour six personnes. Ajoute trois pommes de terre à acheter la semaine prochaine.")
            Accessible.name: I18n.tr("Votre demande")
            wrapMode: TextEdit.WordWrap
            color: Theme.text
            placeholderTextColor: Theme.muted
            selectByMouse: true
            padding: 16
            background: Rectangle {
                color: Theme.surface
                radius: 12
                border.color: request.activeFocus ? Theme.accent : Theme.border
            }
            onTextChanged: page.assistant.discard()
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
            ActionButton {
                objectName: "dictationButton"
                text: page.assistant.recording ? I18n.tr("Arrêter et transcrire") : I18n.tr("Dicter ma demande")
                enabled: !page.assistant.busy
                onClicked: page.assistant.recording ? page.assistant.stopDictation() : page.assistant.startDictation()
            }
            ActionButton {
                visible: page.assistant.recording
                text: I18n.tr("Annuler")
                onClicked: page.assistant.cancelDictation()
            }
            Item {
                Layout.fillWidth: true
            }
            ActionButton {
                objectName: "generatePlanButton"
                text: I18n.tr("Envoyer la demande")
                primary: true
                enabled: request.text.trim().length > 0 && !page.assistant.busy && !page.assistant.recording
                onClicked: page.assistant.plan(request.text)
            }
        }
        Caption {
            text: page.assistant.recording ? I18n.tr("Enregistrement en cours — 20 secondes maximum.") : page.assistant.busy ? page.assistant.status : I18n.tr("Dictée locale avec Parakeet. Le texte et le contexte sont envoyés à GLM pour interprétation.")
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            Accessible.role: Accessible.StaticText
        }
        Panel {
            visible: page.assistant.steps.length > 0 || page.assistant.busy
            Layout.fillWidth: true
            implicitHeight: progressContent.implicitHeight + 32
            ColumnLayout {
                id: progressContent
                anchors.fill: parent
                anchors.margins: 16
                spacing: 10
                RowLayout {
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
        RowLayout {
            Layout.topMargin: 8
            ActionButton {
                text: I18n.tr("Voir mon planning")
                quiet: true
                onClicked: page.planningRequested()
            }
            ActionButton {
                text: I18n.tr("Configurer manuellement")
                quiet: true
                onClicked: page.configureRequested()
            }
        }
    }
    Connections {
        target: page.assistant
        function onTranscribed(text) {
            request.text = request.text.length ? request.text + " " + text : text;
        }

    }
}
