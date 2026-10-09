import QtQuick
import QtQuick.Controls

ActionButton {
    primary: checked
    // Selection belongs to the page state; clicking must not break its binding.
    checkable: false
    Accessible.checkable: true
    Accessible.checked: checked
    implicitHeight: 34
    font.pixelSize: 12
    font.weight: Font.Medium
}
