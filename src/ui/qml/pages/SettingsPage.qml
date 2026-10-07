import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: page
    required property var store
    property var assistant: store.assistant
    clip: true
    contentWidth: availableWidth
    ColumnLayout {
        width: page.availableWidth
        spacing: 20
        Panel {
            Layout.fillWidth: true
            implicitHeight: voiceContent.implicitHeight + 48
            ColumnLayout {
                id: voiceContent
                anchors.fill: parent
                anchors.margins: 24
                spacing: 18
                Heading { text: "Parakeet TDT 0.6B v3" }
                Caption {
                    objectName: "parakeetStatus"
                    text: I18n.tr(page.assistant.modelDownloading ? "Téléchargement du modèle en cours…" : page.assistant.modelInstalled ? "Modèle installé. Vous pouvez dicter votre demande." : "Modèle absent ou incomplet. Téléchargez-le pour utiliser la dictée.")
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
                Caption {
                    text: I18n.tr("Téléchargement depuis Hugging Face : environ 2,6 Go. Une connexion Internet est nécessaire.")
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
                Caption {
                    text: page.assistant.modelPath
                    Layout.fillWidth: true
                    wrapMode: Text.WrapAnywhere
                }
                ActionButton {
                    objectName: "downloadParakeetButton"
                    text: I18n.tr("Télécharger Parakeet")
                    primary: true
                    enabled: !page.assistant.modelInstalled && !page.assistant.busy && !page.assistant.recording
                    onClicked: page.assistant.downloadModel()
                }
                BusyIndicator { running: page.assistant.modelDownloading; visible: running }
                Caption {
                    text: page.assistant.modelError
                    visible: text.length > 0
                    color: Theme.danger
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
            }
        }
        Panel {
            Layout.fillWidth: true
            implicitHeight: content.implicitHeight + 48
            ColumnLayout {
                id: content
                anchors.fill: parent
                anchors.margins: 24
                spacing: 18
                Heading {
                    text: I18n.tr("Langue de l’application")
                    Layout.fillWidth: true
                }
                Caption {
                    text: I18n.tr("L’interface et les recettes changent de langue immédiatement.")
                    Layout.fillWidth: true
                }
                RowLayout {
                    spacing: 10
                    Chip {
                        objectName: "languageFrench"
                        text: "Français"
                        checked: page.store.language === "fr"
                        onClicked: page.store.setLanguage("fr")
                    }
                    Chip {
                        objectName: "languageEnglish"
                        text: "English"
                        checked: page.store.language === "en"
                        onClicked: page.store.setLanguage("en")
                    }
                }
                Caption {
                    text: page.store.configError
                    visible: text.length > 0
                    color: Theme.danger
                    Layout.fillWidth: true
                }
            }
        }
        Panel {
            Layout.fillWidth: true
            implicitHeight: glmContent.implicitHeight + 48
            ColumnLayout {
                id: glmContent
                anchors.fill: parent
                anchors.margins: 24
                spacing: 18
                Heading { text: "GLM_ai · glm-5.3-flash" }
                Caption { text: I18n.tr("Clé API GLM"); Layout.fillWidth: true }
                RowLayout {
                    Layout.fillWidth: true
                    Field {
                        id: apiKey
                        objectName: "glmApiKey"
                        Layout.fillWidth: true
                        text: page.store.glmApiKey
                        placeholderText: I18n.tr("Saisir la clé API")
                        echoMode: reveal.checked ? TextInput.Normal : TextInput.Password
                        inputMethodHints: Qt.ImhSensitiveData | Qt.ImhNoPredictiveText
                    }
                    ActionButton {
                        id: reveal
                        objectName: "glmRevealKey"
                        text: "👁"
                        checkable: true
                        Accessible.name: I18n.tr(checked ? "Masquer la clé" : "Afficher la clé")
                        ToolTip.visible: hovered
                        ToolTip.text: Accessible.name
                    }
                    ActionButton {
                        objectName: "glmSaveKey"
                        text: I18n.tr("Enregistrer")
                        primary: true
                        onClicked: {
                            if (page.store.setGlmApiKey(apiKey.text)) {
                                reveal.checked = false;
                                apiKey.text = page.store.glmApiKey;
                            }
                        }
                    }
                }
                Caption {
                    text: page.store.glmError
                    visible: text.length > 0
                    color: Theme.danger
                    Layout.fillWidth: true
                }
            }
        }
        Item {
            Layout.fillHeight: true
        }
    }
}
