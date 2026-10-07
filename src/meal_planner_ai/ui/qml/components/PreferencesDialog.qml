import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Modal {
    id: dialog
    required property var store
    property bool vegetarian: false
    title: I18n.tr("Les goûts de votre foyer")
    ListModel { id: members }
    function resizeMembers(count) {
        while (members.count < count)
            members.append({name: "", intolerances: ""});
        while (members.count > count)
            members.remove(members.count - 1);
    }
    function save() {
        const profiles = [];
        for (let i = 0; i < members.count; ++i)
            profiles.push({name: members.get(i).name, intolerances: members.get(i).intolerances});
        if (store.setHousehold(profiles, vegetarian, dislikes.text))
            close();
    }
    onOpened: {
        members.clear();
        for (const member of store.settings.members)
            members.append({name: member.name, intolerances: member.intolerances});
        people.value = store.settings.people;
        resizeMembers(people.value);
        vegetarian = store.settings.vegetarian;
        dislikes.text = store.settings.dislikes;
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
                    onValueModified: dialog.resizeMembers(value)
                }
                Caption {
                    Layout.fillWidth: true
                    text: I18n.tr("Les intolérances de chacun s’appliquent à tous les repas du foyer.")
                }
                Repeater {
                    model: members
                    delegate: ColumnLayout {
                        id: memberRow
                        required property int index
                        required property string name
                        required property string intolerances
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
                            objectName: "memberIntolerances-" + memberRow.index
                            Layout.fillWidth: true
                            text: memberRow.intolerances
                            placeholderText: I18n.tr("Ex. lactose, gluten, arachides")
                            maximumLength: 1000
                            Accessible.name: I18n.tr("Intolérances, séparées par des virgules")
                                             + " " + (memberRow.index + 1)
                            onTextEdited: members.setProperty(memberRow.index, "intolerances", text)
                        }
                    }
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
                Caption { text: I18n.tr("Aliments exclus") }
                Field {
                    id: dislikes
                    Layout.fillWidth: true
                    placeholderText: I18n.tr("Ex. champignons, saumon")
                    maximumLength: 1000
                    Accessible.name: I18n.tr("Aliments exclus, séparés par des virgules")
                }
                Caption {
                    text: I18n.tr("Le menu sera actualisé pour tout le foyer. Les invités et les articles cochés seront réinitialisés.")
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
