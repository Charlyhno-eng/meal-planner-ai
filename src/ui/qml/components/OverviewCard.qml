import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: control
    property string iconName: "planning"
    property int count: 0
    implicitHeight: 88
    padding: 14
    hoverEnabled: true
    Accessible.name: count + " " + text
    background: Panel {
        color: control.down ? Theme.raised : Theme.surface
        border.color: control.activeFocus ? Theme.accent : control.hovered ? Theme.borderHover : Theme.border
        border.width: control.activeFocus ? 2 : 1
    }
    contentItem: RowLayout {
        spacing: 12
        Rectangle {
            implicitWidth: 38
            implicitHeight: 38
            radius: 12
            color: Theme.accentDark
            AppIcon {
                anchors.centerIn: parent
                name: control.iconName
                width: 22
                height: 22
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 2
            Text {
                text: control.count
                color: Theme.text
                font.pixelSize: 23
                font.weight: Font.DemiBold
            }
            Caption {
                text: control.text
                Layout.fillWidth: true
                font.pixelSize: 11
            }
        }
        Text {
            text: "↗"
            color: control.hovered || control.activeFocus ? Theme.accent : Theme.muted
            font.pixelSize: 17
        }
    }
}
