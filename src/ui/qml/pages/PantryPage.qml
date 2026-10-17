import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ColumnLayout {
    id: page
    required property var store
    signal foodRequested(var food)
    property string category: "text.all"
    readonly property bool filtering: search.text.trim().length > 0 || category !== "text.all"
    property var filtered: store.pantry.filter(item => (category === "text.all" || item.category === category)
                           && item.name.toLocaleLowerCase().includes(search.text.trim().toLocaleLowerCase(
                                                                         )))
    spacing: 20
    RowLayout {
        Layout.fillWidth: true
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6
            Heading {
                text: I18n.tr("text.what_you_already_have")
                Layout.fillWidth: true
            }
            Caption {
                text: page.store.pantry.length + I18n.tr("text.foods_in_your_pantry")
            }
        }
        ActionButton {
            text: I18n.tr("text.add_food")
            primary: true
            onClicked: page.foodRequested(null)
        }
    }
    Caption {
        text: I18n.tr("text.theoretical_stock_after_all_proposed_meals_including_servings_and")
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }
    Field {
        id: search
        objectName: "pantrySearch"
        Layout.fillWidth: true
        placeholderText: I18n.tr("text.search_for_food")
        Accessible.name: I18n.tr("text.search_the_pantry")
    }
    Flow {
        Layout.fillWidth: true
        spacing: 8
        Repeater {
            model: ["text.all", "Fruits & légumes", "Épicerie", "Produits frais"]
            Chip {
                required property string modelData
                text: I18n.tr(modelData)
                checked: page.category === modelData
                onClicked: page.category = modelData
            }
        }
    }
    ScrollView {
        id: scroll
        Layout.fillWidth: true
        Layout.fillHeight: true
        contentWidth: availableWidth
        clip: true
        ColumnLayout {
            width: scroll.availableWidth
            spacing: 8
            Repeater {
                model: page.filtered
                delegate: Panel {
                    id: foodRow
                    required property var modelData
                    Layout.fillWidth: true
                    implicitHeight: 92
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 16
                        spacing: 16
                        Rectangle {
                            width: 44
                            height: 44
                            radius: 12
                            color: foodRow.modelData.category === "Fruits & légumes" ? "#3a4c3c" :
                                                                                       foodRow.modelData.category
                                                                                       === "Épicerie"
                                                                                       ? "#4c4635" :
                                                                                         "#3c4852"
                            Text {
                                anchors.centerIn: parent
                                text: foodRow.modelData.name.substring(0, 1)
                                font.pixelSize: 20
                                color: Theme.text
                            }
                        }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            Text {
                                text: foodRow.modelData.name
                                color: Theme.text
                                font.pixelSize: 15
                                font.weight: Font.Medium
                                Layout.fillWidth: true
                                elide: Text.ElideRight
                            }
                            Caption {
                                text: I18n.tr(foodRow.modelData.category)
                                font.pixelSize: 12
                            }
                        }
                        ColumnLayout {
                            spacing: 5
                            Caption {
                                text: I18n.tr("text.currently") + foodRow.modelData.quantity
                                color: Theme.text
                            }
                            Caption {
                                objectName: "pantryRemaining-" + foodRow.modelData.id
                                text: I18n.tr("text.after_meals") + foodRow.modelData.remainingQuantity
                                color: Theme.accent
                            }
                        }
                        ActionButton {
                            text: I18n.tr("text.edit")
                            quiet: true
                            onClicked: page.foodRequested(foodRow.modelData)
                            Accessible.name: I18n.tr("text.edit_2") + foodRow.modelData.name
                        }
                    }
                }
            }
            EmptyState {
                objectName: "pantryEmptyState"
                visible: page.filtered.length === 0
                Layout.fillWidth: true
                Layout.topMargin: 48
                title: page.filtering ? I18n.tr("text.no_food_found") : I18n.tr("text.your_pantry_is_empty")
                description: page.filtering ? I18n.tr("text.try_another_name_or_category") : I18n.tr("text.add_some_food_to_get_started")
                actionText: page.filtering ? I18n.tr("text.clear_filters") : I18n.tr("text.add_food_2")
                onActivated: {
                    if (page.filtering) { search.clear(); page.category = "text.all"; search.forceActiveFocus(); }
                    else page.foodRequested(null);
                }
            }
        }
    }
}
