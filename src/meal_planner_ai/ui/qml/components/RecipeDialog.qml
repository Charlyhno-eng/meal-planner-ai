import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Modal {
    id: dialog
    required property var store
    property int mealId: -1
    property var meal: store.meals.find(item => item.id === mealId) || null
    title: I18n.tr("À cuisiner")
    width: Math.min(680, parent.width - 48)
    height: Math.min(740, parent.height - 48)
    function showRecipe(id) {
        mealId = id;
        open();
    }
    contentItem: ScrollView {
        id: scroll
        clip: true
        contentWidth: availableWidth
        ColumnLayout {
            width: scroll.availableWidth
            spacing: 16
            PlateArt {
                Layout.fillWidth: true
                Layout.preferredHeight: 156
                tone: dialog.meal ? dialog.meal.color : "#aabb88"
                variant: dialog.meal ? dialog.meal.art : 0
            }
            Heading {
                text: dialog.meal ? dialog.meal.title : ""
                Layout.fillWidth: true
            }
            Caption {
                text: dialog.meal ? dialog.meal.subtitle : ""
            }
            RowLayout {
                Caption {
                    text: dialog.meal ? dialog.meal.minutes + " min  ·  " + dialog.meal.servings
                                        + I18n.tr(" personnes") : ""
                    color: Theme.accent
                }
                Item {
                    Layout.fillWidth: true
                }
                Caption {
                    text: dialog.meal && dialog.meal.vegetarian ? I18n.tr("Végétarien") : ""
                }
            }
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 1
                color: Theme.border
            }
            Heading {
                text: I18n.tr("Ingrédients")
                font.pixelSize: 17
            }
            Repeater {
                model: dialog.meal ? dialog.meal.ingredients : []
                RowLayout {
                    required property var modelData
                    Layout.fillWidth: true
                    Text {
                        text: parent.modelData.name
                        color: Theme.text
                        font.pixelSize: 14
                        Layout.fillWidth: true
                    }
                    Caption {
                        text: parent.modelData.quantity
                    }
                }
            }
            Heading {
                text: I18n.tr("Préparation")
                font.pixelSize: 17
                Layout.topMargin: 8
            }
            Repeater {
                model: dialog.meal ? dialog.meal.steps : []
                RowLayout {
                    id: step
                    required property string modelData
                    required property int index
                    Layout.fillWidth: true
                    spacing: 12
                    Rectangle {
                        width: 26
                        height: 26
                        radius: 13
                        color: Theme.raised
                        Layout.alignment: Qt.AlignTop
                        Text {
                            anchors.centerIn: parent
                            text: step.index + 1
                            color: Theme.accent
                            font.pixelSize: 12
                        }
                    }
                    Caption {
                        text: step.modelData
                        color: Theme.text
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignVCenter
                        lineHeight: 1.3
                    }
                }
            }
        }
    }
    footer: Item {
        implicitHeight: 74
        RowLayout {
            anchors.fill: parent
            anchors.margins: 16
            ActionButton {
                text: I18n.tr("↻  Changer de repas")
                onClicked: dialog.store.replaceMeal(dialog.mealId)
            }
            Item {
                Layout.fillWidth: true
            }
            ActionButton {
                text: I18n.tr("C’est noté")
                primary: true
                onClicked: dialog.close()
            }
        }
    }
}
