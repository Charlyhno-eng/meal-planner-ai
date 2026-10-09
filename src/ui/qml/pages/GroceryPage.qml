import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ColumnLayout {
    id: page
    required property var store
    signal assistantRequested
    signal pantryRequested
    property bool showAvailable: false
    property var shopping: store.groceries.filter(item => !item.available)
    property int completed: shopping.filter(item => item.checked).length
    property var displayed: store.groceries.filter(item => item.available === showAvailable)
    spacing: 20
    RowLayout {
        Layout.fillWidth: true
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6
            Heading {
                text: I18n.tr("Tout pour vos prochains repas")
                Layout.fillWidth: true
            }
            Caption {
                text: I18n.tr("Les achats ajoutés indiquent leur propre période.")
            }
        }
        ActionButton {
            text: I18n.tr("Copier la liste")
            enabled: page.shopping.length > 0
            onClicked: page.store.copyGroceries()
        }
    }
    Panel {
        Layout.fillWidth: true
        implicitHeight: 92
        RowLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 20
            Rectangle {
                width: 44
                height: 44
                radius: 22
                color: Theme.accentDark
                Text {
                    anchors.centerIn: parent
                    text: "✓"
                    color: Theme.accent
                    font.pixelSize: 22
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 10
                Text {
                    text: page.store.groceries.length === 0 ? I18n.tr("La liste est vide") : page.shopping.length === 0 ? I18n.tr("Vous avez déjà tout !") :
                                                       page.completed === page.shopping.length
                                                       ? I18n.tr("Tout est dans le panier !") :
                                                         page.completed + I18n.tr(" sur ")
                                                         + page.shopping.length + I18n.tr(
                                                             " articles cochés")
                    color: Theme.text
                    font.pixelSize: 15
                    font.weight: Font.Medium
                }
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 5
                    radius: 3
                    color: Theme.border
                    Rectangle {
                        width: parent.width * (page.shopping.length ? page.completed
                                                                      / page.shopping.length : (page.store.groceries.length ? 1 : 0))
                        height: parent.height
                        radius: 3
                        color: Theme.accent
                        Behavior on width {
                            NumberAnimation {
                                duration: Theme.motionDuration
                            }
                        }
                    }
                }
            }
        }
    }
    RowLayout {
        spacing: 8
        Chip {
            text: I18n.tr("À acheter  ·  ") + page.shopping.length
            checked: !page.showAvailable
            onClicked: page.showAvailable = false
        }
        Chip {
            text: I18n.tr("Déjà à la maison  ·  ") + (page.store.groceries.length
                                                      - page.shopping.length)

            checked: page.showAvailable
            onClicked: page.showAvailable = true
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
            spacing: 10
            Repeater {
                model: ["Fruits & légumes", "Épicerie", "Produits frais"]
                delegate: ColumnLayout {
                    id: group
                    required property string modelData
                    property var items: page.displayed.filter(item => item.category === modelData)
                    visible: items.length > 0
                    Layout.fillWidth: true
                    spacing: 6
                    Caption {
                        text: I18n.tr(group.modelData)
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        Layout.topMargin: 10
                        Layout.bottomMargin: 4
                    }
                    Repeater {
                        model: group.items
                        delegate: Panel {
                            id: groceryRow
                            required property var modelData
                            objectName: "grocery-" + modelData.id
                            Layout.fillWidth: true
                            implicitHeight: modelData.requiredQuantity ? 78 : 60
                            color: modelData.checked && !page.showAvailable ? "#283631" :
                                                                              Theme.surface
                            MouseArea {
                                anchors.fill: parent
                                enabled: !page.showAvailable
                                cursorShape: Qt.PointingHandCursor
                                onClicked: page.store.toggleGrocery(groceryRow.modelData.id)
                            }
                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 18
                                spacing: 12
                                CheckBox {
                                    visible: !page.showAvailable
                                    checked: groceryRow.modelData.checked
                                    Accessible.name: groceryRow.modelData.name + ", "
                                                     + groceryRow.modelData.quantity
                                    onClicked: page.store.toggleGrocery(groceryRow.modelData.id)
                                    indicator: Rectangle {
                                        implicitWidth: 22
                                        implicitHeight: 22
                                        x: 8
                                        y: parent.height / 2 - height / 2
                                        radius: 6
                                        color: parent.checked ? Theme.accent : "transparent"
                                        border.color: parent.activeFocus ? Theme.text :
                                                                           parent.checked
                                                                           ? Theme.accent :
                                                                             Theme.muted
                                        border.width: parent.activeFocus ? 2 : 1
                                        Text {
                                            anchors.centerIn: parent
                                            text: "✓"
                                            visible: groceryRow.modelData.checked
                                            color: Theme.accentDark
                                            font.pixelSize: 15
                                        }
                                    }
                                }
                                Text {
                                    visible: page.showAvailable
                                    text: "✓"
                                    color: Theme.accent
                                    font.pixelSize: 18
                                    Layout.leftMargin: 8
                                    Layout.rightMargin: 8
                                }
                                ColumnLayout {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Text {
                                        text: groceryRow.modelData.name + (groceryRow.modelData.periodLabel ? " · " + groceryRow.modelData.periodLabel : "")
                                        color: groceryRow.modelData.checked && !page.showAvailable
                                               ? Theme.muted : Theme.text
                                        font.pixelSize: 14
                                        font.strikeout: groceryRow.modelData.checked &&
                                                        !page.showAvailable
                                        Layout.fillWidth: true
                                        elide: Text.ElideRight
                                    }
                                    Caption {
                                        visible: !!groceryRow.modelData.requiredQuantity
                                        text: I18n.tr("Besoin : ") + (groceryRow.modelData.requiredQuantity || "")
                                              + I18n.tr(" · Réserve : ") + (groceryRow.modelData.stockQuantity || "")
                                        Layout.fillWidth: true
                                        font.pixelSize: 11
                                        elide: Text.ElideRight
                                    }
                                }
                                Caption {
                                    text: groceryRow.modelData.quantity
                                }
                                ActionButton {
                                    visible: !!groceryRow.modelData.requestId
                                    text: I18n.tr("Retirer")
                                    quiet: true
                                    onClicked: page.store.removeRequest(groceryRow.modelData.requestId)
                                }
                            }
                        }
                    }
                }
            }
            EmptyState {
                objectName: "groceryEmptyState"
                visible: page.displayed.length === 0
                Layout.fillWidth: true
                Layout.topMargin: 36
                title: page.showAvailable ? I18n.tr("Rien en réserve pour ces repas") : I18n.tr("La liste est vide")
                description: page.showAvailable ? I18n.tr("Ajoutez vos aliments dans la réserve.") : I18n.tr("Ajoutez des achats dans l’assistant ou les ingrédients manquants depuis une recette.")
                actionText: page.showAvailable ? I18n.tr("Ouvrir la réserve") : I18n.tr("Ajouter des achats")
                onActivated: page.showAvailable ? page.pantryRequested() : page.assistantRequested()
            }
            Caption {
                visible: page.displayed.length > 0
                text: page.showAvailable ? I18n.tr("Quantités nécessaires aux repas, couvertes par votre réserve.") : I18n.tr("Achats ajoutés explicitement. Cocher un article ne modifie pas votre réserve.")
                Layout.topMargin: 12
                Layout.bottomMargin: 12
            }
        }
    }
}
