import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: control
    property string iconName: "meal"
    property bool selected: false
    property int count: 0
    property bool collapsed: false
    implicitWidth: 48
    implicitHeight: 48
    padding: 12
    leftPadding: 12
    rightPadding: 12
    hoverEnabled: true
    Accessible.name: text
    ToolTip.visible: collapsed && hovered
    ToolTip.text: text
    background: Rectangle {
        radius: 11
        color: control.selected ? Theme.selected : control.hovered ? Theme.surface : "transparent"
        border.color: control.activeFocus ? Theme.accent : "transparent"
        border.width: 2
        Behavior on color {
            ColorAnimation {
                duration: Theme.motionDuration
            }
        }
        Rectangle {
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            width: 3
            height: control.selected ? 20 : 0
            radius: 2
            color: Theme.accent
            Behavior on height {
                NumberAnimation {
                    duration: Theme.motionDuration
                    easing.type: Easing.OutCubic
                }
            }
        }
    }
    contentItem: RowLayout {
        spacing: navLabel.visible ? 10 : 0
        clip: true
        AppIcon {
            objectName: "navIcon"
            name: control.iconName
            color: control.selected ? Theme.accent : Theme.muted
            Layout.minimumWidth: 24
            Layout.maximumWidth: 24
            Layout.preferredHeight: 24
        }
        Text {
            id: navLabel
            visible: !control.collapsed && control.width >= 160
            text: control.text
            color: control.selected ? Theme.accent : Theme.muted
            font.pixelSize: 13
            font.weight: control.selected ? Font.DemiBold : Font.Normal
            Layout.fillWidth: true
            Layout.minimumWidth: 0
            elide: Text.ElideRight
        }
        Rectangle {
            visible: navLabel.visible && control.count > 0
            implicitWidth: Math.max(22, countLabel.implicitWidth + 10)
            implicitHeight: 22
            radius: 7
            color: control.selected ? Theme.accentDark : Theme.background
            Text {
                id: countLabel
                anchors.centerIn: parent
                text: control.count
                color: control.selected ? Theme.accent : Theme.muted
                font.pixelSize: 10
            }
        }
    }
}
