import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Modal {
    id: dialog
    required property var store
    noticeSource: store
    title: I18n.tr("text.meal_settings")
    height: Math.min(650, parent.height - 48)
    onOpened: {
        start.iso = store.settings.start;
        days.value = store.settings.days;
        meals.value = store.settings.count;
        people.value = store.settings.people;
        diet.currentIndex = store.settings.vegetarian ? 1 : 0;
        foodsToAvoid.text = store.settings.foods_to_avoid;
    }
    contentItem: ScrollView {
        id: editor
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: editor.availableWidth
            spacing: 16
            Caption {
                text: I18n.tr("text.choose_the_pace_that_suits_you")
            }
            Caption {
                text: I18n.tr("text.starting_on")
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
                        text: I18n.tr("text.days")
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
                        text: I18n.tr("text.meals_2")
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
                        text: I18n.tr("text.people")
                    }
                    NumberPicker {
                        id: people
                        to: 12
                    }
                }
            }
            Caption {
                text: I18n.tr("text.choose_meals_for_the_period_without_assigned_days")
                font.pixelSize: 12
            }
            Caption {
                text: I18n.tr("text.diet_2")
            }
            Choice {
                id: diet
                Layout.fillWidth: true
                model: [I18n.tr("text.varied"), I18n.tr("text.vegetarian")]
            }
            Caption {
                text: I18n.tr("text.foods_the_household_does_not_want_to_eat")
            }
            Field {
                id: foodsToAvoid
                Layout.fillWidth: true
                placeholderText: I18n.tr("text.e_g_mushrooms_salmon")
                Accessible.name: I18n.tr("text.foods_the_household_does_not_want_to_eat")
            }
            Caption {
                text: I18n.tr("text.these_settings_apply_to_future_requests_use_the_assistant")
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
                text: I18n.tr("text.cancel")
                quiet: true
                onClicked: dialog.close()
            }
            ActionButton {
                text: I18n.tr("text.save")
                primary: true
                onClicked: if (dialog.store.configure(start.iso, days.value, meals.value,
                                                      people.value, diet.currentIndex === 1,
                                                      foodsToAvoid.text))
                               dialog.close()
            }
        }
    }
}
