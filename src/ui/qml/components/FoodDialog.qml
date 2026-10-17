import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Modal {
    id: dialog
    required property var store
    noticeSource: store
    property var food: null
    property bool confirming: false
    readonly property real parsedAmount: Number(amount.text.trim().replace(",", "."))
    readonly property bool packaged: quantityMode.currentIndex === 1
    readonly property real packageCount: Number(packages.text.trim())
    readonly property real totalAmount: parsedAmount * (packaged ? packageCount : 1)
    readonly property bool validPackages: !packaged || (/^[0-9]+$/.test(packages.text.trim()) && packageCount > 0 && packageCount <= 100000)
    readonly property bool validAmount: /^[0-9]+([.,][0-9]+)?$/.test(amount.text.trim()) && parsedAmount > 0 && totalAmount <= 100000 && validPackages
    title: food ? I18n.tr("text.edit_food") : I18n.tr("text.add_food_2")
    function edit(item) {
        food = item;
        open();
    }
    onOpened: {
        confirming = false;
        quantityMode.currentIndex = 0;
        packages.text = "";
        name.text = food ? food.name : "";
        amount.text = food ? String(food.amount).replace(".", ",") : "";
        unit.currentIndex = food ? ["g", "ml", "pièce"].indexOf(food.unit) : 0;
        category.currentIndex = food ? ["Fruits & légumes", "Épicerie", "Produits frais"].indexOf(
                                           food.category) : 0;
        name.forceActiveFocus();
    }
    contentItem: ColumnLayout {
        spacing: 16
        Caption {
            text: I18n.tr("text.food")
        }
        Field {
            id: name
            objectName: "foodName"
            Layout.fillWidth: true
            placeholderText: I18n.tr("text.e_g_cherry_tomatoes")
            maximumLength: 80
            Accessible.name: I18n.tr("text.food_name")
        }
        Choice {
            id: quantityMode
            objectName: "foodQuantityMode"
            Layout.fillWidth: true
            model: ["text.total_quantity", "text.boxes_tubs_packets"]
            onCurrentIndexChanged: if (currentIndex === 1 && unit.currentIndex === 2) unit.currentIndex = 0
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 14
            ColumnLayout {
                visible: dialog.packaged
                Layout.preferredWidth: 110
                Caption { text: I18n.tr("text.number_of_packages") }
                Field {
                    id: packages
                    objectName: "foodPackageCount"
                    Layout.fillWidth: true
                    placeholderText: "2"
                    maximumLength: 6
                    inputMethodHints: Qt.ImhDigitsOnly
                    Accessible.name: I18n.tr("text.number_of_packages")
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                Caption {
                    text: dialog.packaged ? I18n.tr("text.per_package") : I18n.tr("text.quantity")
                }
                Field {
                    id: amount
                    objectName: "foodAmount"
                    maximumLength: 16
                    Layout.fillWidth: true
                    placeholderText: dialog.packaged ? "250" : "500"
                    inputMethodHints: Qt.ImhFormattedNumbersOnly
                    Accessible.name: dialog.packaged ? I18n.tr("text.weight_or_volume_per_package") : I18n.tr("text.available_quantity")
                }
            }
            ColumnLayout {
                Layout.preferredWidth: 142
                Caption {
                    text: I18n.tr("text.unit")
                }
                Choice {
                    id: unit
                    objectName: "foodUnit"
                    Layout.fillWidth: true
                    model: dialog.packaged ? ["g", "ml"] : ["g", "ml", "pièce"]
                }
            }
        }
        Caption {
            Layout.fillWidth: true
            text: dialog.packaged ? I18n.tr("text.enter_the_weight_or_volume_of_one_package_e") : I18n.tr("text.for_packaged_foods_choose_boxes_tubs_packets_use_pieces")
        }
        Caption {
            objectName: "foodPackageTotal"
            visible: dialog.packaged && dialog.validAmount
            Layout.fillWidth: true
            color: Theme.accent
            text: I18n.tr("text.total_quantity_2") + dialog.totalAmount.toLocaleString(Qt.locale(), 'g', 8) + " " + unit.currentText
        }
        Caption {
            objectName: "foodAmountHint"
            Layout.fillWidth: true
            text: I18n.tr("text.enter_a_quantity_greater_than_zero_and_no_higher")
            color: amount.text.length > 0 && !dialog.validAmount ? Theme.danger : Theme.muted
        }
        Caption {
            text: I18n.tr("text.category")
        }
        Choice {
            id: category
            Layout.fillWidth: true
            model: ["Fruits & légumes", "Épicerie", "Produits frais"]
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 10
            ActionButton {
                visible: dialog.food !== null
                text: dialog.confirming ? I18n.tr("text.confirm_removal") : I18n.tr("text.remove")
                destructive: true
                quiet: true
                onClicked: {
                    if (!dialog.confirming)
                        dialog.confirming = true;
                    else {
                        dialog.store.removeFood(dialog.food.id);
                        dialog.close();
                    }
                }
            }
            Item {
                Layout.fillWidth: true
            }
            ActionButton {
                text: I18n.tr("text.cancel")
                quiet: true
                onClicked: dialog.close()
            }
            ActionButton {
                text: I18n.tr("text.save")
                primary: true
                objectName: "saveFoodButton"
                enabled: name.text.trim().length > 0 && dialog.validAmount
                onClicked: if (dialog.store.saveFood(dialog.food ? dialog.food.id : -1, name.text, dialog.totalAmount,
                                                     unit.model[unit.currentIndex],
                                                     category.model[category.currentIndex]))
                               dialog.close()
            }
        }
    }
}
