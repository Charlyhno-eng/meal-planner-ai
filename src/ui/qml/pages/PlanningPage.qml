import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: page
    RemovalDialog {
        id: removalDialog
        onConfirmed: function(recordId) { page.store.removeRequest(recordId); }
    }
    onVisibleChanged: if (!visible) removalDialog.close()
    required property var store
    signal configureRequested
    signal recipeRequested(int mealId)
    signal groceriesRequested
    signal assistantRequested
    clip: true
    contentWidth: availableWidth
    ColumnLayout {
        width: page.availableWidth
        spacing: 22
        Panel {
            Layout.fillWidth: true
            implicitHeight: hero.implicitHeight + 40
            color: Theme.hero
            border.color: Theme.borderHover
            RowLayout {
                id: hero
                anchors.fill: parent
                anchors.margins: 20
                spacing: 18
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Caption {
                        text: I18n.tr("text.your_next_meals")
                        color: Theme.accent
                        font.pixelSize: 11
                        font.weight: Font.Medium
                    }
                    Heading {
                        text: I18n.tr("text.meals_made_for_you")
                        Layout.fillWidth: true
                        font.pixelSize: 26
                    }
                    Caption {
                        text: page.store.meals.length + I18n.tr("text.meals")
                              + page.store.settings.people + I18n.tr("suffix.people")

                        color: "#c5d3c6"
                    }
                }
                ActionButton {
                    text: I18n.tr("text.meal_settings")
                    primary: true
                    onClicked: page.configureRequested()
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 5
                Heading {
                    text: I18n.tr("text.on_the_menu")
                    Layout.fillWidth: true
                }
                Caption {
                    text: I18n.tr("text.configured_period") + page.store.period
                }
            }
            ActionButton {
                text: I18n.tr("text.view_groceries_2")
                quiet: true
                onClicked: page.groceriesRequested()
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            visible: page.store.requestedMeals.length > 0
            spacing: 12
            Heading {
                text: I18n.tr("text.meal_requests")
                font.pixelSize: 20
            }
            Caption {
                text: I18n.tr("text.older_requests_without_a_recipe_send_them_again_in")
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }
            Repeater {
                model: page.store.requestedMeals
                delegate: Panel {
                    required property var modelData
                    objectName: "meal-request-" + modelData.id
                    Layout.fillWidth: true
                    implicitHeight: wish.implicitHeight + 32
                    RowLayout {
                        id: wish
                        anchors.fill: parent
                        anchors.margins: 16
                        ColumnLayout {
                            Layout.fillWidth: true
                            Heading {
                                text: modelData.title
                                font.pixelSize: 17
                                Layout.fillWidth: true
                            }
                            Caption {
                                text: modelData.servings + I18n.tr("suffix.servings") + " · " + modelData.periodLabel
                                Layout.fillWidth: true
                            }
                        }
                        ActionButton {
                            text: I18n.tr("text.remove")
                            quiet: true
                            objectName: "removeItemButton"
                            onClicked: removalDialog.request(modelData.id, modelData.title)
                        }
                    }
                }
            }
        }
        GridLayout {
            id: grid
            Layout.fillWidth: true
            columns: page.availableWidth >= 920 ? 3 : 2
            columnSpacing: 16
            rowSpacing: 16
            Repeater {
                model: page.store.meals
                delegate: Panel {
                    id: mealCard
                    required property var modelData
                    required property int index
                    Layout.fillWidth: true
                    Layout.preferredWidth: 260
                    implicitHeight: modelData.requestId ? 354 : 278
                    border.color: cardHover.hovered ? Theme.borderHover : Theme.border
                    HoverHandler {
                        id: cardHover
                    }
                    ColumnLayout {
                        anchors.fill: parent
                        anchors.margins: 15
                        spacing: 10
                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: mealCard.modelData.label
                                color: Theme.text
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                                Layout.fillWidth: true
                            }
                        }
                        PlateArt {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 116
                            tone: mealCard.modelData.color
                            variant: mealCard.modelData.art
                            scale: 1
                        }
                        Text {
                            text: mealCard.modelData.title
                            color: Theme.text
                            font.pixelSize: 16
                            font.weight: Font.DemiBold
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                        }
                        Caption {
                            text: mealCard.modelData.minutes + I18n.tr("unit.minutes") + " · "
                                  + mealCard.modelData.servings + I18n.tr("suffix.servings") + (
                                      mealCard.modelData.guests ? I18n.tr("text.guests") : "")
                            font.pixelSize: 12
                        }
                        Caption {
                            text: mealCard.modelData.periodLabel || ""
                            visible: text.length > 0
                            font.pixelSize: 11
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            ActionButton {
                                text: I18n.tr("text.view_recipe_3")
                                quiet: true
                                implicitHeight: 30
                                padding: 0
                                Layout.fillWidth: true
                                onClicked: page.recipeRequested(mealCard.modelData.id)
                                Accessible.name: I18n.tr("text.view_recipe_2")
                                                 + mealCard.modelData.title
                            }
                            ActionButton {
                                visible: !mealCard.modelData.requestId
                                text: "↻"
                                quiet: true
                                implicitHeight: 32
                                implicitWidth: 32
                                font.pixelSize: 22
                                Accessible.name: I18n.tr("text.replace") + mealCard.modelData.title
                                ToolTip.visible: hovered
                                ToolTip.text: I18n.tr("text.change_meal")
                                onClicked: page.store.replaceMeal(mealCard.modelData.id)
                            }
                        }
                        ActionButton {
                            visible: !!mealCard.modelData.requestId
                            text: I18n.tr("text.remove")
                            quiet: true
                            objectName: "removeItemButton"
                            onClicked: removalDialog.request(mealCard.modelData.requestId, mealCard.modelData.title)
                        }
                    }
                }
            }
        }
        EmptyState {
            visible: page.store.meals.length === 0
            Layout.fillWidth: true
            Layout.topMargin: 24
            title: I18n.tr("text.no_meals_planned_yet")
            description: I18n.tr("text.ask_the_assistant_for_a_dish_to_create_your")
            actionText: I18n.tr("text.plan_a_meal")
            onActivated: page.assistantRequested()
        }
    }
}
