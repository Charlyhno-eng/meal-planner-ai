import QtQuick
import QtQuick.Controls

ComboBox {
    id: control
    implicitHeight: 44
    font.pixelSize: 14
    leftPadding: 14
    rightPadding: 32
    background: Rectangle {
        radius: 9
        color: Theme.background
        border.color: control.activeFocus || control.hovered ? Theme.accent : Theme.border
        border.width: control.activeFocus ? 2 : 1
    }
    contentItem: Text {
        text: I18n.tr(control.displayText)
        color: Theme.text
        font: control.font
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
    indicator: Text {
        x: parent.width - 24
        anchors.verticalCenter: parent.verticalCenter
        text: "⌄"
        color: Theme.muted
    }
    delegate: ItemDelegate {
        width: control.width
        text: control.textRole ? modelData[control.textRole] : modelData
        highlighted: control.highlightedIndex === index
        contentItem: Text {
            text: I18n.tr(parent.text)
            color: Theme.text
            font.pixelSize: 14
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            color: parent.highlighted ? Theme.raised : Theme.surface
        }
    }
    popup: Popup {
        y: control.height + 4
        width: control.width
        padding: 4
        implicitHeight: Math.min(contentItem.implicitHeight + 8, 240)
        background: Rectangle {
            color: Theme.surface
            radius: 10
            border.color: Theme.border
        }
        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            ScrollIndicator.vertical: ScrollIndicator {}
        }
    }
}
