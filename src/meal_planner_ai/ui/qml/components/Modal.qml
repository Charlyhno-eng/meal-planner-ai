import QtQuick
import QtQuick.Controls

Dialog {
    id: control
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(560, parent.width - 48)
    modal: true
    focus: true
    padding: 24
    topPadding: 18
    closePolicy: Popup.CloseOnEscape
    enter: Transition {
        NumberAnimation { property: "opacity"; from: 0; to: 1; duration: Theme.motionDuration }
    }
    background: Rectangle {
        color: Theme.surface
        radius: 18
        border.color: Theme.border
    }
    header: Item {
        implicitHeight: 70
        Heading {
            anchors.left: parent.left
            anchors.leftMargin: 24
            anchors.verticalCenter: parent.verticalCenter
            text: control.title
            width: parent.width - 88
        }
        ActionButton {
            text: "×"
            quiet: true
            font.pixelSize: 24
            anchors.right: parent.right
            anchors.rightMargin: 12
            anchors.verticalCenter: parent.verticalCenter
            Accessible.name: I18n.tr("Fermer")
            onClicked: control.close()
        }
    }
    Overlay.modal: Rectangle {
        color: "#aa151d21"
    }
}
