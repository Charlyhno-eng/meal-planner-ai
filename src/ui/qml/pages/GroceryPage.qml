import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ColumnLayout {
    id: page
    RemovalDialog {
        id: removalDialog
        onConfirmed: function(recordId) { page.store.removeRequest(recordId); }
    }
    onVisibleChanged: if (!visible) removalDialog.close()
    required property var store
    signal assistantRequested
    signal pantryRequested
    property bool showAvailable: false
    property var shopping: store.groceries.filter(item => !item.available)
    property int completed: shopping.filter(item => item.checked).length
    property var displayed: store.groceries.filter(item => item.available === showAvailable)
    spacing: 20
    RowLayout {
        Layout.fillWidth: true
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6
            Heading {
                text: I18n.tr("text.everything_for_your_next_meals")
                Layout.fillWidth: true
            }
            Caption {
                text: I18n.tr("text.added_purchases_show_their_own_planning_period")
            }
        }
        ActionButton {
            objectName: "finishGroceriesButton"
            text: I18n.tr("text.finish_shopping")
            enabled: page.completed > 0
            onClicked: page.store.finishGroceries()
        }
        ActionButton {
            text: I18n.tr("text.copy_list")
            enabled: page.shopping.length > 0
            onClicked: page.store.copyGroceries()
        }
    }
    Panel {
        Layout.fillWidth: true
        implicitHeight: 92
        RowLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 20
            Rectangle {
                width: 44
                height: 44
                radius: 22
                color: Theme.accentDark
                Text {
                    anchors.centerIn: parent
                    text: "✓"
                    color: Theme.accent
                    font.pixelSize: 22
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 10
                Text {
                    text: page.store.groceries.length === 0 ? I18n.tr("text.the_list_is_empty") : page.shopping.length === 0 ? I18n.tr("text.you_already_have_everything") :
                                                       page.completed === page.shopping.length
                                                       ? I18n.tr("text.everything_is_in_your_basket") :
                                                         page.completed + I18n.tr("text.of")
                                                         + page.shopping.length + I18n.tr(
                                                             "text.items_checked")
                    color: Theme.text
                    font.pixelSize: 15
                    font.weight: Font.Medium
                }
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 5
                    radius: 3
                    color: Theme.border
                    Rectangle {
                        width: parent.width * (page.shopping.length ? page.completed
                                                                      / page.shopping.length : (page.store.groceries.length ? 1 : 0))
                        height: parent.height
                        radius: 3
                        color: Theme.accent
                        Behavior on width {
                            NumberAnimation {
                                duration: Theme.motionDuration
                            }
                        }
                    }
                }
            }
        }
    }
    RowLayout {
        spacing: 8
        Chip {
            text: I18n.tr("text.to_buy") + page.shopping.length
            checked: !page.showAvailable
            onClicked: page.showAvailable = false
        }
        Chip {
            text: I18n.tr("text.already_at_home") + (page.store.groceries.length
                                                      - page.shopping.length)

            checked: page.showAvailable
            onClicked: page.showAvailable = true
        }
    }
    ScrollView {
        id: scroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        contentWidth: availableWidth
        clip: true
        ColumnLayout {
            width: scroll.availableWidth
            spacing: 10
            Repeater {
                model: ["Fruits & légumes", "Épicerie", "Produits frais"]
                delegate: ColumnLayout {
                    id: group
                    required property string modelData
                    property var items: page.displayed.filter(item => item.category === modelData)
                    visible: items.length > 0
                    Layout.fillWidth: true
                    spacing: 6
                    Caption {
                        text: I18n.tr(group.modelData)
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        Layout.topMargin: 10
                        Layout.bottomMargin: 4
                    }
                    Repeater {
                        model: group.items
                        delegate: Panel {
                            id: groceryRow
                            required property var modelData
                            objectName: "grocery-" + modelData.id
                            Layout.fillWidth: true
                            implicitHeight: modelData.requiredQuantity ? 78 : 60
                            color: modelData.checked && !page.showAvailable ? "#283631" :
                                                                              Theme.surface
                            MouseArea {
                                anchors.fill: parent
                                enabled: !page.showAvailable
                                cursorShape: Qt.PointingHandCursor
                                onClicked: page.store.toggleGrocery(groceryRow.modelData.id)
                            }
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 18
                                spacing: 12
                                CheckBox {
                                    visible: !page.showAvailable
                                    checked: groceryRow.modelData.checked
                                    Accessible.name: groceryRow.modelData.name + ", "
                                                     + groceryRow.modelData.quantity
                                    onClicked: page.store.toggleGrocery(groceryRow.modelData.id)
                                    indicator: Rectangle {
                                        implicitWidth: 22
                                        implicitHeight: 22
                                        x: 8
                                        y: parent.height / 2 - height / 2
                                        radius: 6
                                        color: parent.checked ? Theme.accent : "transparent"
                                        border.color: parent.activeFocus ? Theme.text :
                                                                           parent.checked
                                                                           ? Theme.accent :
                                                                             Theme.muted
                                        border.width: parent.activeFocus ? 2 : 1
                                        Text {
                                            anchors.centerIn: parent
                                            text: "✓"
                                            visible: groceryRow.modelData.checked
                                            color: Theme.accentDark
                                            font.pixelSize: 15
                                        }
                                    }
                                }
                                Text {
                                    visible: page.showAvailable
                                    text: "✓"
                                    color: Theme.accent
                                    font.pixelSize: 18
                                    Layout.leftMargin: 8
                                    Layout.rightMargin: 8
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Text {
                                        text: groceryRow.modelData.name + (groceryRow.modelData.periodLabel ? " · " + groceryRow.modelData.periodLabel : "")
                                        color: groceryRow.modelData.checked && !page.showAvailable
                                               ? Theme.muted : Theme.text
                                        font.pixelSize: 14
                                        font.strikeout: groceryRow.modelData.checked &&
                                                        !page.showAvailable
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                    }
                                    Caption {
                                        visible: !!groceryRow.modelData.requiredQuantity
                                        text: I18n.tr("text.required") + (groceryRow.modelData.requiredQuantity || "")
                                              + I18n.tr("text.pantry_2") + (groceryRow.modelData.stockQuantity || "")
                                        Layout.fillWidth: true
                                        font.pixelSize: 11
                                        elide: Text.ElideRight
                                    }
                                }
                                Caption {
                                    text: groceryRow.modelData.quantity
                                }
                                ActionButton {
                                    visible: !!groceryRow.modelData.requestId
                                    text: I18n.tr("text.remove")
                                    quiet: true
                                    objectName: "removeItemButton"
                                    onClicked: removalDialog.request(groceryRow.modelData.requestId, groceryRow.modelData.name)
                                }
                            }
                        }
                    }
                }
            }
            EmptyState {
                objectName: "groceryEmptyState"
                visible: page.displayed.length === 0
                Layout.fillWidth: true
                Layout.topMargin: 36
                title: page.showAvailable ? I18n.tr("text.nothing_in_stock_for_these_meals") : I18n.tr("text.the_list_is_empty")
                description: page.showAvailable ? I18n.tr("text.add_your_food_to_the_pantry") : I18n.tr("text.add_purchases_in_the_assistant_or_missing_ingredients_from")
                actionText: page.showAvailable ? I18n.tr("text.open_pantry") : I18n.tr("text.add_purchases")
                onActivated: page.showAvailable ? page.pantryRequested() : page.assistantRequested()
            }
            Caption {
                visible: page.displayed.length > 0
                text: page.showAvailable ? I18n.tr("text.quantities_needed_for_meals_covered_by_your_pantry") : I18n.tr("text.finish_shopping_to_add_checked_items_to_your_pantry")
                Layout.topMargin: 12
                Layout.bottomMargin: 12
            }
        }
    }
}
