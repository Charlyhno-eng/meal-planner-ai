import QtQuick
import QtQuick.Layouts

Modal {
    id: dialog
    property var targetId: null
    property string itemName: ""
    signal confirmed(var recordId)
    objectName: "removalDialog"
    title: I18n.tr("Confirmer le retrait")
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
            text: I18n.tr("Voulez-vous vraiment retirer cet élément ?") + "\n" + dialog.itemName
        }
        RowLayout {
            Layout.alignment: Qt.AlignRight
            ActionButton {
                objectName: "cancelRemovalButton"
                text: I18n.tr("Annuler")
                quiet: true
                onClicked: dialog.close()
            }
            ActionButton {
                objectName: "confirmRemovalButton"
                text: I18n.tr("Confirmer le retrait")
                destructive: true
                onClicked: {
                    dialog.confirmed(dialog.targetId);
                    dialog.close();
                }
            }
        }
    }
}
