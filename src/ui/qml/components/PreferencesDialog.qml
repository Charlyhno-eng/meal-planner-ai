import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Modal {
    id: dialog
    required property var store
    noticeSource: store
    property bool vegetarian: false
    title: I18n.tr("Les goûts de votre foyer")
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
                Caption { text: I18n.tr("Personnes au quotidien") }
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
                        Caption { text: I18n.tr("Personne ") + (memberRow.index + 1) }
                        Field {
                            objectName: "memberName-" + memberRow.index
                            Layout.fillWidth: true
                            text: memberRow.name
                            placeholderText: I18n.tr("Nom")
                            maximumLength: 100
                            Accessible.name: I18n.tr("Nom") + " " + (memberRow.index + 1)
                            onTextEdited: members.setProperty(memberRow.index, "name", text)
                        }
                        Field {
                            objectName: "memberFoodsToAvoid-" + memberRow.index
                            Layout.fillWidth: true
                            text: memberRow.foodsToAvoid
                            placeholderText: I18n.tr("Aliments que cette personne ne veut pas manger (séparés par des virgules)")
                            maximumLength: 1000
                            onTextEdited: members.setProperty(memberRow.index, "foodsToAvoid", text)
                        }
                    }
                }
                ActionButton {
                    objectName: "addHouseholdMember"
                    text: I18n.tr("Ajouter une personne")
                    enabled: people.value < 12
                    onClicked: people.increase()
                }
                Caption { text: I18n.tr("Alimentation") }
                RowLayout {
                    spacing: 8
                    Chip {
                        text: I18n.tr("Variée")
                        checked: !dialog.vegetarian
                        onClicked: dialog.vegetarian = false
                    }
                    Chip {
                        text: I18n.tr("Végétarienne")
                        checked: dialog.vegetarian
                        onClicked: dialog.vegetarian = true
                    }
                }
                Caption { text: I18n.tr("Aliments que le foyer ne veut pas manger") }
                Caption {
                    Layout.fillWidth: true
                    text: I18n.tr("Cette liste s’applique à tout le foyer.")
                }
                FoodTags {
                    id: exclusions
                    objectName: "householdExclusions"
                    Layout.fillWidth: true
                }
                Caption {
                    text: I18n.tr("Les préférences s’appliquent à tout le foyer. Les recettes existantes doivent être compatibles. Les articles cochés seront réinitialisés.")
                    Layout.fillWidth: true
                    font.pixelSize: 12
                }
            }
        }
        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            ActionButton {
                text: I18n.tr("Annuler")
                quiet: true
                onClicked: dialog.close()
            }
            ActionButton {
                objectName: "saveHousehold"
                text: I18n.tr("Enregistrer")
                primary: true
                onClicked: dialog.save()
            }
        }
    }
}
