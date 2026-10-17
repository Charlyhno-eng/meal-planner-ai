import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: page
    required property var store
    property var assistant: store.assistant
    function showDictation() {
        Qt.callLater(function() {
            page.contentItem.contentY = Math.min(voicePanel.y, Math.max(0, page.contentItem.contentHeight - page.availableHeight));
            downloadButton.forceActiveFocus();
        });
    }
    clip: true
    contentWidth: availableWidth
    ColumnLayout {
        width: page.availableWidth
        spacing: 20
        Panel {
            Layout.fillWidth: true
            implicitHeight: glmContent.implicitHeight + 48
            ColumnLayout {
                id: glmContent
                anchors.fill: parent
                anchors.margins: 24
                spacing: 18
                Heading { text: I18n.tr("text.assistant_connection") }
                Caption { text: I18n.tr("model.glm") }
                Caption { text: I18n.tr("text.glm_api_key"); Layout.fillWidth: true }
                RowLayout {
                    Layout.fillWidth: true
                    Field {
                        id: apiKey
                        objectName: "glmApiKey"
                        Layout.fillWidth: true
                        text: page.store.glmApiKey
                        placeholderText: I18n.tr("text.enter_api_key")
                        echoMode: reveal.checked ? TextInput.Normal : TextInput.Password
                        inputMethodHints: Qt.ImhSensitiveData | Qt.ImhNoPredictiveText
                    }
                    ActionButton {
                        id: reveal
                        objectName: "glmRevealKey"
                        text: "👁"
                        checkable: true
                        Accessible.name: I18n.tr(checked ? "text.hide_key" : "text.show_key")
                        ToolTip.visible: hovered
                        ToolTip.text: Accessible.name
                    }
                    ActionButton {
                        objectName: "glmSaveKey"
                        text: I18n.tr("text.save")
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
        Panel {
            Layout.fillWidth: true
            id: voicePanel
            implicitHeight: voiceContent.implicitHeight + 48
            ColumnLayout {
                id: voiceContent
                anchors.fill: parent
                anchors.margins: 24
                spacing: 18
                Heading { text: I18n.tr("text.voice_dictation") }
                Caption { text: I18n.tr("model.parakeet") }
                Caption {
                    objectName: "parakeetStatus"
                    text: I18n.tr(page.assistant.modelDownloading ? "text.downloading_model" : page.assistant.modelInstalled ? "text.model_installed_you_can_dictate_your_request" : "text.model_missing_or_incomplete_download_it_to_use_dictation")
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
                Caption {
                    text: I18n.tr("text.download_from_hugging_face_about_2_6_gb_an")
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
                Caption {
                    text: page.assistant.modelPath
                    Layout.fillWidth: true
                    wrapMode: Text.WrapAnywhere
                }
                ActionButton {
                    id: downloadButton
                    objectName: "downloadParakeetButton"
                    text: I18n.tr("text.download_parakeet")
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
        Item {
            Layout.fillHeight: true
        }
    }
}
