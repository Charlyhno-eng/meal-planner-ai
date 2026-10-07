import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: page
    objectName: "assistantPage"
    required property var store
    property var assistant: store.assistant
    readonly property bool compact: height < 680
    signal planningRequested
    signal pantryRequested
    signal groceriesRequested
    signal configureRequested
    clip: true
    contentWidth: availableWidth

    ColumnLayout {
        width: page.availableWidth
        spacing: page.compact ? 12 : 18
        Panel {
            Layout.fillWidth: true
            implicitHeight: welcome.implicitHeight + (page.compact ? 32 : 40)
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: Theme.hero }
                GradientStop { position: 1; color: Theme.surface }
            }
            border.color: Theme.borderHover
            RowLayout {
                id: welcome
                anchors.fill: parent
                anchors.margins: page.compact ? 16 : 20
                spacing: 20
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: page.compact ? 8 : 10
                    Caption {
                        text: I18n.tr("VOTRE CUISINE, CONNECTÉE")
                        color: Theme.accent
                        font.pixelSize: 10
                        font.letterSpacing: 1.5
                    }
                    Heading {
                        text: I18n.tr("Bien manger. Tout simplement.")
                        font.pixelSize: page.compact ? 24 : page.availableWidth < 800 ? 27 : 32
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        elide: Text.ElideNone
                    }
                    Caption {
                        text: I18n.tr("Vos repas, vos réserves et vos courses, réunis au même endroit.")
                        Layout.fillWidth: true
                        color: Theme.text
                        wrapMode: Text.WordWrap
                    }
                    Caption {
                        text: page.store.period + "  ·  " + page.store.settings.people + I18n.tr(" personnes")
                        color: Theme.accent
                        font.pixelSize: 12
                        Layout.fillWidth: true
                    }
                }
                KitchenArt {
                    Layout.preferredWidth: page.availableWidth < 800 ? 150 : 210
                    Layout.preferredHeight: page.compact ? 104 : 156
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 12
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
        Panel {
            Layout.fillWidth: true
            implicitHeight: composer.implicitHeight + (page.compact ? 32 : 40)
            ColumnLayout {
                id: composer
                anchors.fill: parent
                anchors.margins: page.compact ? 16 : 20
                spacing: page.compact ? 10 : 12
                RowLayout {
                    Layout.fillWidth: true
                    AppIcon {
                        name: "assistant"
                        color: Theme.secondary
                        Layout.preferredWidth: 22
                        Layout.preferredHeight: 22
                    }
                    Heading {
                        text: I18n.tr("Que souhaitez-vous organiser ?")
                        font.pixelSize: 20
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                    }
                }
                Caption {
                    text: I18n.tr("Décrivez un repas à préparer, un achat à ajouter ou les aliments disponibles.")
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
                Caption {
                    text: I18n.tr("Une demande valide ajoute directement vos repas, leurs recettes et les courses nécessaires.")
                    Layout.fillWidth: true
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                }
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    enabled: !page.assistant.busy && !page.assistant.recording
                    Caption { text: I18n.tr("Essayez :"); font.pixelSize: 12 }
                    Repeater {
                        model: [
                            { label: I18n.tr("Un repas"), prompt: I18n.tr("Je veux faire un tiramisu pour six personnes.") },
                            { label: I18n.tr("Des courses"), prompt: I18n.tr("Ajoute trois pommes de terre à acheter la semaine prochaine.") },
                            { label: I18n.tr("Ma réserve"), prompt: I18n.tr("J’ai 500 g de riz.") }
                        ]
                        ActionButton {
                            required property var modelData
                            required property int index
                            objectName: "requestExample" + index
                            text: modelData.label
                            quiet: true
                            implicitHeight: 32
                            font.pixelSize: 12
                            Accessible.description: modelData.prompt
                            ToolTip.visible: hovered
                            ToolTip.text: modelData.prompt
                            onClicked: {
                                request.text = modelData.prompt;
                                request.forceActiveFocus();
                                request.cursorPosition = request.length;
                            }
                        }
                    }
                    Item { Layout.fillWidth: true }
                }
                TextArea {
                    id: request
                    objectName: "planningRequest"
                    Layout.fillWidth: true
                    Layout.preferredHeight: page.compact ? 90 : 112
                    enabled: !page.assistant.busy && !page.assistant.recording
                    placeholderText: I18n.tr("Ex. Je veux faire un tiramisu pour six personnes.")
                    Accessible.name: I18n.tr("Votre demande")
                    wrapMode: TextEdit.WordWrap
                    color: Theme.text
                    placeholderTextColor: Theme.muted
                    selectionColor: Theme.accent
                    selectedTextColor: Theme.accentDark
                    selectByMouse: true
                    padding: 16
                    background: Rectangle {
                        color: Theme.background
                        radius: 12
                        border.color: request.activeFocus ? Theme.accent : Theme.border
                        border.width: request.activeFocus ? 2 : 1
                        Behavior on border.color {
                            ColorAnimation { duration: Theme.motionDuration }
                        }
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
                        quiet: true
                        onClicked: page.assistant.cancelDictation()
                    }
                    Item { Layout.fillWidth: true }
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
                    font.pixelSize: 11
                    wrapMode: Text.WordWrap
                    Accessible.role: Accessible.StaticText
                }
            }
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
