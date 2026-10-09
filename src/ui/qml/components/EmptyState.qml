import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: control
    property string title: ""
    property string description: ""
    property string actionText: ""
    signal activated
    spacing: 12
    Heading {
        text: control.title
        Layout.fillWidth: true
        horizontalAlignment: Text.AlignHCenter
        wrapMode: Text.WordWrap
        elide: Text.ElideNone
    }
    Caption {
        text: control.description
        Layout.fillWidth: true
        horizontalAlignment: Text.AlignHCenter
    }
    ActionButton {
        visible: control.actionText.length > 0
        text: control.actionText
        primary: true
        Layout.alignment: Qt.AlignHCenter
        onClicked: control.activated()
    }
}
