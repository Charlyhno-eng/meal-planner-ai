import QtQuick
import QtQuick.Controls

Button {
    id: control
    property bool primary: false
    property bool quiet: false
    property bool destructive: false
    implicitHeight: 44
    implicitWidth: Math.max(42, contentItem.implicitWidth + 30)
    padding: 12
    hoverEnabled: true
    font.pixelSize: 14
    font.weight: Font.DemiBold
    Accessible.name: text
    scale: down && !Theme.reducedMotion ? 0.98 : 1
    Behavior on scale {
        NumberAnimation { duration: Theme.reducedMotion ? 0 : 90; easing.type: Easing.OutCubic }
    }
    background: Rectangle {
        radius: 10
        color: !control.enabled ? (control.primary ? Theme.selected : Theme.surface)
             : control.primary ? (control.down ? Theme.accent : control.hovered ? Theme.accentHover : Theme.accent)
             : control.down ? Theme.border : control.hovered ? Theme.raised
             : control.quiet ? "transparent" : Theme.surface
        border.color: !control.enabled && control.primary ? Theme.border
                    : control.activeFocus ? (control.primary ? Theme.text : Theme.accent)
                    : control.quiet || control.primary ? "transparent"
                    : control.hovered ? Theme.borderHover : Theme.border
        border.width: control.activeFocus ? 2 : 1
        Behavior on color {
            ColorAnimation {
                duration: Theme.motionDuration
            }
        }
        Behavior on border.color {
            ColorAnimation { duration: Theme.motionDuration }
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
