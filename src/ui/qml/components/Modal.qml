import QtQuick
import QtQuick.Controls

Dialog {
    id: control
    property var noticeSource: null
    property string feedback: ""
    onAboutToShow: feedback = ""
    Connections {
        target: control.noticeSource
        function onNotice(message) { if (control.visible) control.feedback = message; }
    }
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
        implicitHeight: 70 + (feedbackText.visible ? feedbackText.implicitHeight + 16 : 0)
        Heading {
            anchors.left: parent.left
            anchors.leftMargin: 24
            y: 24
            text: control.title
            width: parent.width - 88
        }
        ActionButton {
            text: "×"
            quiet: true
            font.pixelSize: 24
            anchors.right: parent.right
            anchors.rightMargin: 12
            y: 12
            Accessible.name: I18n.tr("Fermer")
            onClicked: control.close()
        }
        Caption {
            id: feedbackText
            objectName: "dialogFeedback"
            x: 24
            y: 66
            width: parent.width - 48
            text: control.feedback
            visible: text.length > 0
            color: Theme.text
            Accessible.role: Accessible.AlertMessage
            Accessible.name: text
        }
    }
    Overlay.modal: Rectangle {
        color: "#aa151d21"
    }
}
