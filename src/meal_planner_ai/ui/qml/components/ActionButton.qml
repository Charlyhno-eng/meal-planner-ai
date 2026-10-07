import QtQuick
import QtQuick.Controls

Button {
    id: control
    property bool primary: false
    property bool quiet: false
    property bool destructive: false
    implicitHeight: 42
    implicitWidth: Math.max(42, contentItem.implicitWidth + 30)
    padding: 12
    hoverEnabled: true
    font.pixelSize: 14
    font.weight: Font.DemiBold
    Accessible.name: text
    background: Rectangle {
        radius: 10
        color: !control.enabled ? Theme.surface : control.down ? Theme.border : control.primary ? (
                                                                                                      control.hovered
                                                                                                      ? "#c9e8b0" :
                                                                                                        Theme.accent) :
                                                                                                  control.hovered
                                                                                                  ? Theme.raised :
                                                                                                    control.quiet
                                                                                                    ? "transparent" :
                                                                                                      Theme.surface
        border.color: control.activeFocus ? Theme.accent : control.quiet || control.primary ? "transparent" :
                                                                                              Theme.border
        border.width: control.activeFocus ? 2 : 1
        Behavior on color {
            ColorAnimation {
                duration: 100
            }
        }
    }
    contentItem: Text {
        text: control.text
        font: control.font
        color: !control.enabled ? Theme.muted : control.primary ? Theme.accentDark :
                                                                  control.destructive
                                                                  ? Theme.danger : Theme.text
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
