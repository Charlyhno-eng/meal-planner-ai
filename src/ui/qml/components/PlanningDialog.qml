import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Modal {
    id: dialog
    required property var store
    noticeSource: store
    title: I18n.tr("Paramètres des repas")
    height: Math.min(650, parent.height - 48)
    onOpened: {
        start.iso = store.settings.start;
        days.value = store.settings.days;
        meals.value = store.settings.count;
        people.value = store.settings.people;
        diet.currentIndex = store.settings.vegetarian ? 1 : 0;
        dislikes.text = store.settings.dislikes;
    }
    contentItem: ScrollView {
        id: editor
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: editor.availableWidth
            spacing: 16
            Caption {
                text: I18n.tr("Choisissez le rythme qui vous convient.")
            }
            Caption {
                text: I18n.tr("À partir du")
            }
            DatePicker {
                id: start
                Layout.fillWidth: true
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: 24
                ColumnLayout {
                    Layout.fillWidth: true
                    Caption {
                        text: I18n.tr("Jours")
                    }
                    NumberPicker {
                        id: days
                        objectName: "planningDays"
                        to: 14
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Caption {
                        text: I18n.tr("Repas")
                    }
                    NumberPicker {
                        id: meals
                        objectName: "planningMealCount"
                        to: 28
                    }
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Caption {
                        text: I18n.tr("Personnes")
                    }
                    NumberPicker {
                        id: people
                        to: 12
                    }
                }
            }
            Caption {
                text: I18n.tr("Choisissez vos repas pour la période, sans jour imposé.")
                font.pixelSize: 12
            }
            Caption {
                text: I18n.tr("Alimentation")
            }
            Choice {
                id: diet
                Layout.fillWidth: true
                model: [I18n.tr("Variée"), I18n.tr("Végétarienne")]
            }
            Caption {
                text: I18n.tr("Aliments exclus")
            }
            Field {
                id: dislikes
                Layout.fillWidth: true
                placeholderText: I18n.tr("Ex. champignons, saumon")
                Accessible.name: I18n.tr("Aliments exclus, séparés par des virgules")
            }
            Caption {
                text: I18n.tr("Ces réglages serviront aux prochaines demandes. Pour créer des recettes, utilisez l’assistant. Les articles cochés seront réinitialisés.")
                Layout.fillWidth: true
                font.pixelSize: 12
            }
        }
    }
    footer: Item {
        implicitHeight: 76
        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
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
                onClicked: if (dialog.store.configure(start.iso, days.value, meals.value,
                                                      people.value, diet.currentIndex === 1,
                                                      dislikes.text))
                               dialog.close()
            }
        }
    }
}
