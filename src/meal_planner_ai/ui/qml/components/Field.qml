import QtQuick
import QtQuick.Controls

TextField {
    id: control
    implicitHeight: 44
    color: Theme.text
    placeholderTextColor: Theme.muted
    selectionColor: Theme.accent
    selectedTextColor: Theme.accentDark
    font.pixelSize: 14
    leftPadding: 14
    rightPadding: 14
    background: Rectangle {
        radius: 9
        color: Theme.background
        border.color: control.activeFocus ? Theme.accent : Theme.border
        border.width: control.activeFocus ? 2 : 1
    }
}
