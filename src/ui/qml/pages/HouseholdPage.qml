import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"

ScrollView {
    id: page
    RemovalDialog {
        id: removalDialog
        onConfirmed: function(recordId) { if (String(recordId).startsWith("group:")) page.store.removeGuestGroup(Number(String(recordId).slice(6))); else page.store.setGuests(Number(recordId), 0); }
    }
    onVisibleChanged: if (!visible) removalDialog.close()
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
                text: I18n.tr("text.a_place_at_the_table_for_everyone")
            }
            Caption {
                text: I18n.tr("text.your_household_your_tastes_your_guests")
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
                            text: I18n.tr("text.your_household")
                            font.pixelSize: 18
                            Layout.fillWidth: true
                        }
                        Caption {
                            text: page.store.settings.people + I18n.tr("text.people_every_day")
                        }
                    }
                    ActionButton {
                        text: I18n.tr("text.edit")
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
                            text: profile.modelData.name || (I18n.tr("prefix.person") + (profile.index + 1))
                            color: Theme.text
                            font.pixelSize: 16
                            font.weight: Font.DemiBold
                            wrapMode: Text.WordWrap
                        }
                        Caption {
                            Layout.fillWidth: true
                            text: profile.modelData.foods_to_avoid
                            visible: text.length > 0
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
                            text: I18n.tr("text.diet_2")
                            font.pixelSize: 11
                            font.weight: Font.Medium
                        }
                        Text {
                            text: page.store.settings.vegetarian ? I18n.tr("text.vegetarian") : I18n.tr(
                                                                       "text.varied")
                            color: Theme.text
                            font.pixelSize: 15
                        }
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        Caption {
                            text: I18n.tr("text.foods_the_household_does_not_want_to_eat")
                            font.pixelSize: 11
                            font.weight: Font.Medium
                        }
                        FoodTags {
                            id: excludedTags
                            Layout.fillWidth: true
                            editable: false
                            function refresh() {
                                load([page.store.settings.foods_to_avoid].concat(
                                    page.store.settings.members.map(member => member.foods_to_avoid)));
                            }
                            Component.onCompleted: refresh()
                            Connections {
                                target: page.store
                                function onSettingsChanged() { excludedTags.refresh(); }
                            }
                        }

                    }
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Heading {
                text: I18n.tr("text.guests_2")
                Layout.fillWidth: true
                font.pixelSize: 20
            }
            ActionButton {
                text: I18n.tr("text.invite_to_a_meal")
                objectName: "addGuestGroupButton"
                onClicked: page.guestRequested()
            }
        }
        Panel {
            visible: page.store.guests.length === 0 && page.store.settings.guest_groups.length === 0
            Layout.fillWidth: true
            implicitHeight: 138
            ColumnLayout {
                anchors.centerIn: parent
                spacing: 12
                Heading {
                    text: I18n.tr("text.room_for_one_more")
                    font.pixelSize: 18
                    Layout.alignment: Qt.AlignHCenter
                }
                Caption {
                    text: I18n.tr("text.servings_adjust_to_your_guests_then_check_which_ingredients")
                    Layout.alignment: Qt.AlignHCenter
                }
                ActionButton {
                    text: I18n.tr("text.add_guests")
                    quiet: true
                    Layout.alignment: Qt.AlignHCenter
                    onClicked: page.guestRequested()
                }
            }
        }
        Repeater {
            model: page.store.settings.guest_groups
            delegate: Panel {
                id: groupRow
                required property var modelData
                required property int index
                Layout.fillWidth: true
                implicitHeight: groupContent.implicitHeight + 36
                ColumnLayout {
                    id: groupContent
                    anchors.fill: parent
                    anchors.margins: 18
                    RowLayout {
                        Layout.fillWidth: true
                        Heading {
                            Layout.fillWidth: true
                            font.pixelSize: 18
                            text: groupRow.modelData.name || I18n.tr("text.guests_2")
                        }
                        ActionButton {
                            text: I18n.tr("text.remove")
                            quiet: true
                            destructive: true
                            objectName: "removeGuestGroupButton"
                            onClicked: removalDialog.request("group:" + groupRow.index, groupRow.modelData.name || I18n.tr("text.guests_2"))
                        }
                    }
                    Caption {
                        Layout.fillWidth: true
                        text: groupRow.modelData.members.length + I18n.tr("suffix.guests") + groupRow.modelData.meals.map(i => I18n.tr("prefix.meal") + (i + 1)).join(", ")
                    }
                    Caption {
                        Layout.fillWidth: true
                        text: I18n.tr("text.preferences_apply_only_to_the_selected_meals")
                    }
                    Repeater {
                        model: groupRow.modelData.members
                        delegate: Caption {
                            required property var modelData
                            required property int index
                            Layout.fillWidth: true
                            text: (modelData.name || I18n.tr("prefix.person") + (index + 1)) + (modelData.foods_to_avoid ? " · " + modelData.foods_to_avoid : "")
                        }
                    }
                }
            }
        }
        Repeater {
            model: page.store.guests.filter(meal => meal.guests > page.store.settings.guest_groups.reduce((total, group) => total + (group.meals.indexOf(meal.id) >= 0 ? group.members.length : 0), 0))
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
                            text: guestRow.modelData.guests + I18n.tr("suffix.guests")
                                  + guestRow.modelData.servings + I18n.tr("text.servings_in_total")
                        }
                    }
                    ActionButton {
                        text: I18n.tr("text.remove")
                        quiet: true
                        destructive: true
                        objectName: "removeItemButton"
                        onClicked: removalDialog.request(guestRow.modelData.id, guestRow.modelData.title)
                    }
                }
            }
        }
    }
}
