import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Modal {
    id: dialog
    required property var store
    noticeSource: store
    title: I18n.tr("Inviter à un repas")
    onOpened: {
        count.value = 2;
        meal.currentIndex = 0;
    }
    contentItem: ColumnLayout {
        spacing: 16
        Caption {
            text: I18n.tr("Quel repas ?")
        }
        Choice {
            id: meal
            Layout.fillWidth: true
            model: dialog.store.meals.map(item => item.label + " · " + item.title)
        }
        Caption {
            text: I18n.tr("Personnes supplémentaires")
        }
        NumberPicker {
            id: count
            to: 12
        }
        Caption {
            text: I18n.tr("Les quantités seront ajustées pour ce repas.")
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 12
            Item {
                Layout.fillWidth: true
            }
            ActionButton {
                text: I18n.tr("Annuler")
                quiet: true
                onClicked: dialog.close()
            }
            ActionButton {
                text: I18n.tr("Ajouter les invités")
                enabled: meal.currentIndex >= 0 && meal.currentIndex < dialog.store.meals.length
                primary: true
                onClicked: {
                    dialog.store.setGuests(dialog.store.meals[meal.currentIndex].id, count.value);
                    dialog.close();
                }
            }
        }
    }
}
