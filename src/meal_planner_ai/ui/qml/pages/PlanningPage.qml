import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: page
    required property var store
    signal configureRequested
    signal recipeRequested(int mealId)
    signal groceriesRequested
    clip: true
    contentWidth: availableWidth
    ColumnLayout {
        width: page.availableWidth
        spacing: 22
        Panel {
            Layout.fillWidth: true
            implicitHeight: hero.implicitHeight + 40
            color: "#30413b"
            border.color: "#485c4e"
            RowLayout {
                id: hero
                anchors.fill: parent
                anchors.margins: 20
                spacing: 18
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Caption {
                        text: I18n.tr("À TABLE, L’ESPRIT TRANQUILLE")
                        color: Theme.accent
                        font.pixelSize: 11
                        font.letterSpacing: 1.2
                    }
                    Heading {
                        text: I18n.tr("Des repas à votre goût.")
                        Layout.fillWidth: true
                        font.pixelSize: 26
                    }
                    Caption {
                        text: page.store.meals.length + I18n.tr(" repas · ")
                              + page.store.settings.people + I18n.tr(" personnes")

                        color: "#c5d3c6"
                    }
                }
                ActionButton {
                    text: I18n.tr("Ajuster le planning")
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
                    text: I18n.tr("Au menu")
                    Layout.fillWidth: true
                }
                Caption {
                    text: I18n.tr("Période configurée : ") + page.store.period
                }
            }
            ActionButton {
                text: I18n.tr("Voir les courses  →")
                quiet: true
                onClicked: page.groceriesRequested()
            }
        }
        ColumnLayout {
            Layout.fillWidth: true
            visible: page.store.requestedMeals.length > 0
            spacing: 12
            Heading {
                text: I18n.tr("Repas souhaités")
                font.pixelSize: 20
            }
            Caption {
                text: I18n.tr("Anciennes demandes sans recette. Envoyez-les à nouveau dans l’assistant pour les planifier.")
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
                                text: modelData.servings + I18n.tr(" pers.") + " · " + modelData.periodLabel
                                Layout.fillWidth: true
                            }
                        }
                        ActionButton {
                            text: I18n.tr("Retirer")
                            quiet: true
                            onClicked: page.store.removeRequest(modelData.id)
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
                    border.color: cardHover.hovered ? "#738775" : Theme.border
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
                            text: mealCard.modelData.minutes + " min · "
                                  + mealCard.modelData.servings + I18n.tr(" pers.") + (
                                      mealCard.modelData.guests ? I18n.tr(" · invités") : "")
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
                                text: I18n.tr("Voir la recette  ↗")
                                quiet: true
                                implicitHeight: 30
                                padding: 0
                                Layout.fillWidth: true
                                onClicked: page.recipeRequested(mealCard.modelData.id)
                                Accessible.name: I18n.tr("Voir la recette : ")
                                                 + mealCard.modelData.title
                            }
                            ActionButton {
                                visible: !mealCard.modelData.requestId
                                text: "↻"
                                quiet: true
                                implicitHeight: 32
                                implicitWidth: 32
                                font.pixelSize: 22
                                Accessible.name: I18n.tr("Remplacer ") + mealCard.modelData.title
                                ToolTip.visible: hovered
                                ToolTip.text: I18n.tr("Changer de repas")
                                onClicked: page.store.replaceMeal(mealCard.modelData.id)
                            }
                        }
                        ActionButton {
                            visible: !!mealCard.modelData.requestId
                            text: I18n.tr("Retirer")
                            quiet: true
                            onClicked: page.store.removeRequest(mealCard.modelData.requestId)
                        }
                    }
                }
            }
        }
        Caption {
            visible: page.store.meals.length === 0
            text: I18n.tr("Aucun repas planifié pour le moment.")
            Layout.bottomMargin: 8
        }
    }
}
