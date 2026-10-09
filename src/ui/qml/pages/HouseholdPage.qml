import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: page
    required property var store
    signal preferencesRequested
    signal guestRequested
    clip: true
    contentWidth: availableWidth
    ColumnLayout {
        width: page.availableWidth
        spacing: 24
        ColumnLayout {
            spacing: 6
            Heading {
                text: I18n.tr("Chacun a sa place à table")
            }
            Caption {
                text: I18n.tr("Votre foyer, vos goûts, vos invités.")
            }
        }
        Panel {
            Layout.fillWidth: true
            implicitHeight: family.implicitHeight + 40
            ColumnLayout {
                id: family
                anchors.fill: parent
                anchors.margins: 20
                spacing: 20
                RowLayout {
                    Layout.fillWidth: true
                    Rectangle {
                        width: 48
                        height: 48
                        radius: 16
                        color: "#3e4e43"
                        Text {
                            anchors.centerIn: parent
                            text: page.store.settings.people
                            color: Theme.accent
                            font.pixelSize: 22
                            font.weight: Font.DemiBold
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        Heading {
                            text: I18n.tr("Votre foyer")
                            font.pixelSize: 18
                            Layout.fillWidth: true
                        }
                        Caption {
                            text: page.store.settings.people + I18n.tr(" personnes au quotidien")
                        }
                    }
                    ActionButton {
                        text: I18n.tr("Modifier")
                        onClicked: page.preferencesRequested()
                    }
                }
                Caption {
                    Layout.fillWidth: true
                    visible: page.store.householdError.length > 0
                    text: page.store.householdError
                    color: Theme.muted
                }
                Repeater {
                    model: page.store.settings.members
                    delegate: ColumnLayout {
                        id: profile
                        required property var modelData
                        required property int index
                        Layout.fillWidth: true
                        spacing: 6
                        Text {
                            Layout.fillWidth: true
                            text: profile.modelData.name || (I18n.tr("Personne ") + (profile.index + 1))
                            color: Theme.text
                            font.pixelSize: 16
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }
                        Caption {
                            Layout.fillWidth: true
                            text: I18n.tr("Intolérances : ") + (profile.modelData.intolerances || I18n.tr("Aucune"))
                        }
                    }
                }
                Rectangle {
                    Layout.fillWidth: true
                    implicitHeight: 1
                    color: Theme.border
                }
                RowLayout {
                    Layout.fillWidth: true
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        Caption {
                            Layout.fillWidth: true
                            text: I18n.tr("Alimentation")
                            font.pixelSize: 11
                            font.weight: Font.Medium
                        }
                        Text {
                            text: page.store.settings.vegetarian ? I18n.tr("Végétarienne") : I18n.tr(
                                                                       "Variée")
                            color: Theme.text
                            font.pixelSize: 15
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        Caption {
                            text: I18n.tr("Aliments exclus")
                            font.pixelSize: 11
                            font.weight: Font.Medium
                        }
                        Text {
                            text: page.store.settings.dislikes || I18n.tr("Aucun")
                            color: Theme.text
                            font.pixelSize: 15
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                        }
                    }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Heading {
                text: I18n.tr("Les invités")
                Layout.fillWidth: true
                font.pixelSize: 20
            }
            ActionButton {
                text: I18n.tr("+  Inviter à un repas")
                enabled: page.store.meals.length > 0
                onClicked: page.guestRequested()
            }
        }
        Panel {
            visible: page.store.guests.length === 0
            Layout.fillWidth: true
            implicitHeight: 138
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 12
                Heading {
                    text: I18n.tr("Une place en plus ?")
                    font.pixelSize: 18
                    Layout.alignment: Qt.AlignHCenter
                }
                Caption {
                    text: page.store.meals.length ? I18n.tr("Les portions s’adaptent à vos invités. Vérifiez ensuite les ingrédients à acheter.") : I18n.tr("Planifiez un repas avant d’ajouter des invités.")
                    Layout.alignment: Qt.AlignHCenter
                }
                ActionButton {
                    text: I18n.tr("Ajouter des invités")
                    enabled: page.store.meals.length > 0
                    quiet: true
                    Layout.alignment: Qt.AlignHCenter
                    onClicked: page.guestRequested()
                }
            }
        }
        Repeater {
            model: page.store.guests
            delegate: Panel {
                id: guestRow
                required property var modelData
                Layout.fillWidth: true
                implicitHeight: 86
                RowLayout {
                    anchors.fill: parent
                    anchors.margins: 18
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 6
                        Text {
                            text: guestRow.modelData.label + " · " + guestRow.modelData.title
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            color: Theme.text
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                        }
                        Caption {
                            text: guestRow.modelData.guests + I18n.tr(" invité(s) · ")
                                  + guestRow.modelData.servings + I18n.tr(" portions au total")
                        }
                    }
                    ActionButton {
                        text: I18n.tr("Retirer")
                        quiet: true
                        destructive: true
                        onClicked: page.store.setGuests(guestRow.modelData.id, 0)
                    }
                }
            }
        }
    }
}
