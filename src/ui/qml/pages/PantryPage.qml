import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ColumnLayout {
    id: page
    required property var store
    signal foodRequested(var food)
    property string category: "Tout"
    readonly property bool filtering: search.text.trim().length > 0 || category !== "Tout"
    property var filtered: store.pantry.filter(item => (category === "Tout" || item.category === category)
                           && item.name.toLocaleLowerCase().includes(search.text.trim().toLocaleLowerCase(
                                                                         )))
    spacing: 20
    RowLayout {
        Layout.fillWidth: true
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6
            Heading {
                text: I18n.tr("Ce que vous avez déjà")
                Layout.fillWidth: true
            }
            Caption {
                text: page.store.pantry.length + I18n.tr(" aliments dans votre réserve")
            }
        }
        ActionButton {
            text: I18n.tr("+  Ajouter un aliment")
            primary: true
            onClicked: page.foodRequested(null)
        }
    }
    Caption {
        text: I18n.tr("Reste théorique après tous les repas proposés, portions et invités inclus. Les achats ne sont pas inclus ; votre réserve actuelle reste inchangée.")
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }
    Field {
        id: search
        objectName: "pantrySearch"
        Layout.fillWidth: true
        placeholderText: I18n.tr("Rechercher un aliment…")
        Accessible.name: I18n.tr("Rechercher dans la réserve")
    }
    Flow {
        Layout.fillWidth: true
        spacing: 8
        Repeater {
            model: ["Tout", "Fruits & légumes", "Épicerie", "Produits frais"]
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
                                text: I18n.tr("Actuellement : ") + foodRow.modelData.quantity
                                color: Theme.text
                            }
                            Caption {
                                objectName: "pantryRemaining-" + foodRow.modelData.id
                                text: I18n.tr("Après les repas : ") + foodRow.modelData.remainingQuantity
                                color: Theme.accent
                            }
                        }
                        ActionButton {
                            text: I18n.tr("Modifier")
                            quiet: true
                            onClicked: page.foodRequested(foodRow.modelData)
                            Accessible.name: I18n.tr("Modifier ") + foodRow.modelData.name
                        }
                    }
                }
            }
            EmptyState {
                objectName: "pantryEmptyState"
                visible: page.filtered.length === 0
                Layout.fillWidth: true
                Layout.topMargin: 48
                title: page.filtering ? I18n.tr("Aucun aliment trouvé") : I18n.tr("Votre réserve est vide")
                description: page.filtering ? I18n.tr("Essayez un autre nom ou une autre catégorie.") : I18n.tr("Ajoutez quelques aliments pour commencer.")
                actionText: page.filtering ? I18n.tr("Effacer les filtres") : I18n.tr("Ajouter un aliment")
                onActivated: {
                    if (page.filtering) { search.clear(); page.category = "Tout"; search.forceActiveFocus(); }
                    else page.foodRequested(null);
                }
            }
        }
    }
}
