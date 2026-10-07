import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Button {
    id: node
    required property string title
    required property string kind
    required property int step
    property color tint: Theme.accent
    property bool selected: false
    property bool planned: false
    property real nodeWidth: 176
    width: nodeWidth
    height: 108
    padding: 12
    hoverEnabled: true
    Accessible.name: title
    Accessible.description: kind === "pantry" ? I18n.tr("Service local")
                                           : I18n.tr("Afficher le rôle et les échanges prévus de cet agent")
    Accessible.role: Accessible.Button
    Accessible.onPressAction: clicked()
    background: Rectangle {
        radius: 16
        color: node.selected ? "#35453d" : node.hovered ? Theme.raised : Theme.surface
        border.color: node.selected || node.activeFocus ? node.tint : Theme.border
        border.width: node.selected || node.activeFocus ? 2 : 1
        Behavior on color { ColorAnimation { duration: 180 } }
        Behavior on border.color { ColorAnimation { duration: 180 } }
    }
    contentItem: ColumnLayout {
        spacing: 8
        RowLayout {
            Layout.fillWidth: true
            Rectangle {
                width: 36
                height: 36
                radius: 10
                color: Qt.rgba(node.tint.r, node.tint.g, node.tint.b, 0.12)
                AgentIcon {
                    anchors.centerIn: parent
                    width: 27
                    height: 27
                    kind: node.kind
                    ink: node.tint
                }
            }
            Item { Layout.fillWidth: true }
            Text {
                visible: node.kind !== "pantry"
                text: node.planned ? I18n.tr("À venir") : "0" + node.step
                font.pixelSize: node.planned ? 10 : 12
                font.weight: Font.DemiBold
                color: node.selected ? node.tint : Theme.muted
            }
        }
        Text {
            Layout.fillWidth: true
            text: node.title
            color: Theme.text
            font.pixelSize: 13
            font.weight: Font.DemiBold
            wrapMode: Text.WordWrap
            Layout.fillHeight: true
            verticalAlignment: Text.AlignVCenter
        }
    }
}
