import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Modal {
    id: dialog
    required property var store
    property bool vegetarian: false
    title: I18n.tr("Les goûts de votre foyer")
    onOpened: {
        people.value = store.settings.people;
        vegetarian = store.settings.vegetarian;
        dislikes.text = store.settings.dislikes;
    }
    contentItem: ColumnLayout {
        spacing: 18
        Caption {
            text: I18n.tr("Personnes au quotidien")
        }
        NumberPicker {
            id: people
            to: 12
        }
        Caption {
            text: I18n.tr("Alimentation")
        }
        RowLayout {
            spacing: 8
            Chip {
                text: I18n.tr("Variée")
                checked: !dialog.vegetarian
                onClicked: dialog.vegetarian = false
            }
            Chip {
                text: I18n.tr("Végétarienne")
                checked: dialog.vegetarian
                onClicked: dialog.vegetarian = true
            }
        }
        Caption {
            text: I18n.tr("Aliments exclus")
        }
        Field {
            id: dislikes
            Layout.fillWidth: true
            placeholderText: I18n.tr("Ex. champignons, saumon")
            maximumLength: 200
            Accessible.name: I18n.tr("Aliments exclus, séparés par des virgules")
        }
        Caption {
            text: I18n.tr(
                      "Le menu sera actualisé pour tout le foyer. Les invités et les articles cochés seront réinitialisés.")
            Layout.fillWidth: true
            font.pixelSize: 12
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 8
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
                onClicked: if (dialog.store.configure(dialog.store.settings.start,
                                                      dialog.store.settings.days,
                                                      dialog.store.settings.count, people.value,
                                                      dialog.vegetarian, dislikes.text))
                               dialog.close()
            }
        }
    }
}
