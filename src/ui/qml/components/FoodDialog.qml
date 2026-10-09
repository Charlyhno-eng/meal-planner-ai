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
    readonly property bool validAmount: /^[0-9]+([.,][0-9]+)?$/.test(amount.text.trim()) && parsedAmount > 0 && parsedAmount <= 100000
    title: food ? I18n.tr("Modifier l’aliment") : I18n.tr("Ajouter un aliment")
    function edit(item) {
        food = item;
        open();
    }
    onOpened: {
        confirming = false;
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
            text: I18n.tr("Aliment")
        }
        Field {
            id: name
            objectName: "foodName"
            Layout.fillWidth: true
            placeholderText: I18n.tr("Ex. Tomates cerises")
            maximumLength: 80
            Accessible.name: I18n.tr("Nom de l’aliment")
        }
        RowLayout {
            Layout.fillWidth: true
            spacing: 14
            ColumnLayout {
                Layout.fillWidth: true
                Caption {
                    text: I18n.tr("Quantité")
                }
                Field {
                    id: amount
                    objectName: "foodAmount"
                    maximumLength: 16
                    Layout.fillWidth: true
                    placeholderText: "500"
                    inputMethodHints: Qt.ImhFormattedNumbersOnly
                    Accessible.name: I18n.tr("Quantité disponible")
                }
            }
            ColumnLayout {
                Layout.preferredWidth: 142
                Caption {
                    text: I18n.tr("Unité")
                }
                Choice {
                    id: unit
                    Layout.fillWidth: true
                    model: ["g", "ml", "pièce"]
                }
            }
        }
        Caption {
            objectName: "foodAmountHint"
            Layout.fillWidth: true
            text: I18n.tr("Saisissez une quantité entre 0 et 100 000, supérieure à zéro.")
            color: amount.text.length > 0 && !dialog.validAmount ? Theme.danger : Theme.muted
        }
        Caption {
            text: I18n.tr("Catégorie")
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
                text: dialog.confirming ? I18n.tr("Confirmer le retrait") : I18n.tr("Retirer")
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
                text: I18n.tr("Annuler")
                quiet: true
                onClicked: dialog.close()
            }
            ActionButton {
                text: I18n.tr("Enregistrer")
                primary: true
                objectName: "saveFoodButton"
                enabled: name.text.trim().length > 0 && dialog.validAmount
                onClicked: if (dialog.store.saveFood(dialog.food ? dialog.food.id : -1, name.text, Number(
                                                         amount.text.replace(",", ".")),
                                                     unit.model[unit.currentIndex],
                                                     category.model[category.currentIndex]))
                               dialog.close()
            }
        }
    }
}
