import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Modal {
    id: dialog
    required property var store
    noticeSource: store
    property bool vegetarian: false
    title: I18n.tr("text.your_household_s_tastes")
    ListModel { id: members }
    function resizeMembers(count) {
        while (members.count < count)
            members.append({name: "", foodsToAvoid: ""});
        while (members.count > count)
            members.remove(members.count - 1);
    }
    function save() {
        const profiles = [];
        for (let i = 0; i < members.count; ++i)
            profiles.push({name: members.get(i).name, foods_to_avoid: members.get(i).foodsToAvoid});
        exclusions.addPending();
        if (store.setHousehold(profiles, vegetarian, exclusions.items.join(", ")))
            close();
    }
    onOpened: {
        members.clear();
        for (const member of store.settings.members)
            members.append({name: member.name, foodsToAvoid: member.foods_to_avoid});
        people.value = store.settings.people;
        resizeMembers(people.value);
        vegetarian = store.settings.vegetarian;
        exclusions.load([store.settings.foods_to_avoid]);
    }
    contentItem: ColumnLayout {
        spacing: 18
        ScrollView {
            id: editor
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(400, dialog.parent.height - 240)
            contentWidth: availableWidth
            clip: true
            ColumnLayout {
                width: editor.availableWidth
                spacing: 14
                Caption { text: I18n.tr("text.people_every_day_2") }
                NumberPicker {
                    id: people
                    objectName: "householdPeople"
                    to: 12
                    onValueChanged: dialog.resizeMembers(value)
                }
                Repeater {
                    model: members
                    delegate: ColumnLayout {
                        id: memberRow
                        required property int index
                        required property string name
                        required property string foodsToAvoid
                        Layout.fillWidth: true
                        spacing: 6
                        Caption { text: I18n.tr("prefix.person") + (memberRow.index + 1) }
                        Field {
                            objectName: "memberName-" + memberRow.index
                            Layout.fillWidth: true
                            text: memberRow.name
                            placeholderText: I18n.tr("text.name")
                            maximumLength: 100
                            Accessible.name: I18n.tr("text.name") + " " + (memberRow.index + 1)
                            onTextEdited: members.setProperty(memberRow.index, "name", text)
                        }
                        Field {
                            objectName: "memberFoodsToAvoid-" + memberRow.index
                            Layout.fillWidth: true
                            text: memberRow.foodsToAvoid
                            placeholderText: I18n.tr("text.foods_this_person_does_not_want_to_eat_comma")
                            maximumLength: 1000
                            onTextEdited: members.setProperty(memberRow.index, "foodsToAvoid", text)
                        }
                    }
                }
                ActionButton {
                    objectName: "addHouseholdMember"
                    text: I18n.tr("text.add_a_person")
                    enabled: people.value < 12
                    onClicked: people.increase()
                }
                Caption { text: I18n.tr("text.diet_2") }
                RowLayout {
                    spacing: 8
                    Chip {
                        text: I18n.tr("text.varied")
                        checked: !dialog.vegetarian
                        onClicked: dialog.vegetarian = false
                    }
                    Chip {
                        text: I18n.tr("text.vegetarian")
                        checked: dialog.vegetarian
                        onClicked: dialog.vegetarian = true
                    }
                }
                Caption { text: I18n.tr("text.foods_the_household_does_not_want_to_eat") }
                Caption {
                    Layout.fillWidth: true
                    text: I18n.tr("text.this_list_applies_to_everyone_in_the_household")
                }
                FoodTags {
                    id: exclusions
                    objectName: "householdExclusions"
                    Layout.fillWidth: true
                }
                Caption {
                    text: I18n.tr("text.preferences_apply_to_the_whole_household_existing_recipes_must")
                    Layout.fillWidth: true
                    font.pixelSize: 12
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            ActionButton {
                text: I18n.tr("text.cancel")
                quiet: true
                onClicked: dialog.close()
            }
            ActionButton {
                objectName: "saveHousehold"
                text: I18n.tr("text.save")
                primary: true
                onClicked: dialog.save()
            }
        }
    }
}
