import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Modal {
    id: dialog
    required property var store
    noticeSource: store
    property int mealId: -1
    property var meal: store.meals.find(item => item.id === mealId) || null
    title: I18n.tr("text.time_to_cook")
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
                wrapMode: Text.WordWrap
                elide: Text.ElideNone
                Layout.fillWidth: true
            }
            Caption {
                text: dialog.meal ? dialog.meal.subtitle : ""
            }
            RowLayout {
                Caption {
                    text: dialog.meal ? dialog.meal.minutes + I18n.tr("unit.minutes") + "  ·  " + dialog.meal.servings
                                        + I18n.tr("suffix.people") : ""
                    color: Theme.accent
                }
                Item {
                    Layout.fillWidth: true
                }
                Caption {
                    text: dialog.meal && dialog.meal.vegetarian ? I18n.tr("text.vegetarian_2") : ""
                }
            }
            Caption {
                objectName: "recipeGuests"
                Layout.fillWidth: true
                visible: !!dialog.meal && dialog.meal.guestNames.length > 0
                text: I18n.tr("text.guests_at_this_meal") + (dialog.meal ? dialog.meal.guestNames.join(", ") : "")
            }
            Caption {
                objectName: "recipeExclusions"
                Layout.fillWidth: true
                visible: !!dialog.meal && dialog.meal.foodsToAvoid.length > 0
                text: I18n.tr("text.foods_to_avoid_for_this_meal") + (dialog.meal ? dialog.meal.foodsToAvoid.join(", ") : "")
            }
            RowLayout {
                visible: !!dialog.meal && !!dialog.meal.requestId
                Layout.fillWidth: true
                Caption {
                    text: I18n.tr("text.servings_excluding_guests")
                    Layout.fillWidth: true
                }
                NumberPicker {
                    objectName: "mealServingsPicker"
                    from: 1
                    to: 32
                    value: dialog.meal ? (dialog.meal.baseServings || 1) : 1
                    Accessible.name: I18n.tr("text.servings_excluding_guests")
                    onValueModified: {
                        if (!dialog.store.setMealServings(dialog.mealId, value))
                            value = dialog.meal.baseServings;
                    }
                }
            }
            Rectangle {
                Layout.fillWidth: true
                implicitHeight: 1
                color: Theme.border
            }
            Heading {
                text: I18n.tr("text.ingredients")
                font.pixelSize: 17
            }
            Repeater {
                model: dialog.meal ? dialog.meal.ingredients : []
                RowLayout {
                    id: ingredientRow
                    required property int index
                    required property var modelData
                    Layout.fillWidth: true
                    Text {
                        text: parent.modelData.name
                        wrapMode: Text.WordWrap
                        color: Theme.text
                        font.pixelSize: 14
                        Layout.fillWidth: true
                    }
                    Caption {
                        text: parent.modelData.quantity
                    }
                    Repeater {
                        model: [
                            { label: I18n.tr("text.pantry"), covered: ingredientRow.modelData.inPantry },
                            { label: I18n.tr("text.groceries"), covered: ingredientRow.modelData.inGroceries }
                        ]
                        Label {
                            required property var modelData
                            text: modelData.label + " " + (modelData.covered ? "✓" : "·")
                            color: modelData.covered ? Theme.accent : Theme.muted
                            font.pixelSize: 11
                            Accessible.name: text
                        }
                    }
                    ActionButton {
                        objectName: "add-ingredient-" + ingredientRow.index
                        visible: ingredientRow.modelData.missingAmount > 0.000000001
                        text: "+"
                        quiet: true
                        implicitHeight: 32
                        Accessible.name: I18n.tr("text.add_to_groceries") + " : " + ingredientRow.modelData.name
                        ToolTip.visible: hovered
                        ToolTip.text: I18n.tr("text.add_to_groceries")
                        onClicked: dialog.store.addIngredientToGroceries(dialog.mealId, ingredientRow.index)
                    }
                }
            }
            Heading {
                text: I18n.tr("text.preparation")
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
                visible: !!dialog.meal && !dialog.meal.requestId
                text: I18n.tr("text.change_meal_2")
                onClicked: dialog.store.replaceMeal(dialog.mealId)
            }
            Item {
                Layout.fillWidth: true
            }
            ActionButton {
                text: I18n.tr("text.got_it")
                primary: true
                onClicked: dialog.close()
            }
        }
    }
}
