import QtQuick
import QtQuick.Controls

SpinBox {
    id: control
    from: 1
    to: 14
    implicitWidth: 142
    implicitHeight: 44
    font.pixelSize: 16
    background: Rectangle {
        color: Theme.background
        radius: 9
        border.color: control.activeFocus ? Theme.accent : Theme.border
    }
    contentItem: Text {
        text: control.value
        color: Theme.text
        font: control.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
    up.indicator: Rectangle {
        x: control.width - width
        width: 40
        height: control.height
        radius: 9
        color: control.up.pressed ? Theme.border : Theme.raised
        Text {
            anchors.centerIn: parent
            text: "+"
            font.pixelSize: 20
            color: control.up.enabled ? Theme.text : Theme.muted
        }
    }
    down.indicator: Rectangle {
        width: 40
        height: control.height
        radius: 9
        color: control.down.pressed ? Theme.border : Theme.raised
        Text {
            anchors.centerIn: parent
            text: "−"
            font.pixelSize: 20
            color: control.down.enabled ? Theme.text : Theme.muted
        }
    }
}
