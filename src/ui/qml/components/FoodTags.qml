import QtQuick
import QtQuick.Layouts

ColumnLayout {
    id: control
    property var items: []
    property bool editable: true
    function load(values) {
        const result = [];
        for (const value of values) {
            for (const term of value.split(",")) {
                const food = term.trim();
                if (food && !result.some(item => item.toLocaleLowerCase() === food.toLocaleLowerCase()))
                    result.push(food);
            }
        }
        items = result;
        input.text = "";
    }
    function addPending() {
        load(items.concat([input.text]));
    }
    spacing: 8
    Flow {
        Layout.fillWidth: true
        spacing: 6
        Repeater {
            model: control.items
            delegate: Chip {
                required property string modelData
                required property int index
                text: modelData + (control.editable ? "  ×" : "")
                implicitWidth: Math.min(contentItem.implicitWidth + 30, control.width)
                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: Theme.text
                    wrapMode: Text.WrapAnywhere
                    verticalAlignment: Text.AlignVCenter
                }
                implicitHeight: Math.max(34, contentItem.implicitHeight + 16)
                Accessible.name: control.editable ? I18n.tr("text.remove") + " " + modelData : modelData
                onClicked: {
                    if (control.editable)
                        control.items = control.items.filter((_, i) => i !== index);
                }
            }
        }
    }
    RowLayout {
        visible: control.editable
        Layout.fillWidth: true
        Field {
            id: input
            objectName: "excludedFoodInput"
            Layout.fillWidth: true
            placeholderText: I18n.tr("text.e_g_lactose_mushrooms")
            Accessible.name: I18n.tr("text.food_to_avoid")
            maximumLength: 1000
            onAccepted: control.addPending()
        }
        ActionButton {
            objectName: "addExcludedFood"
            text: I18n.tr("text.add")
            enabled: input.text.trim().length > 0
            onClicked: control.addPending()
        }
    }
}
