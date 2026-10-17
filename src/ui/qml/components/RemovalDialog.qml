import QtQuick
import QtQuick.Layouts

Modal {
    id: dialog
    property var targetId: null
    property string itemName: ""
    signal confirmed(var recordId)
    objectName: "removalDialog"
    title: I18n.tr("text.confirm_removal")
    function request(recordId, name) {
        targetId = recordId;
        itemName = name;
        open();
    }
    onAboutToHide: targetId = null
    contentItem: ColumnLayout {
        spacing: 20
        Caption {
            Layout.fillWidth: true
            text: I18n.tr("text.are_you_sure_you_want_to_remove_this_item") + "\n" + dialog.itemName
        }
        RowLayout {
            Layout.alignment: Qt.AlignRight
            ActionButton {
                objectName: "cancelRemovalButton"
                text: I18n.tr("text.cancel")
                quiet: true
                onClicked: dialog.close()
            }
            ActionButton {
                objectName: "confirmRemovalButton"
                text: I18n.tr("text.confirm_removal")
                destructive: true
                onClicked: {
                    dialog.confirmed(dialog.targetId);
                    dialog.close();
                }
            }
        }
    }
}
