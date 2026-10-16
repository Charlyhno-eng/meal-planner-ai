import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Modal {
    id: dialog
    required property var store
    noticeSource: store
    title: I18n.tr("Ajouter un groupe d’invités")
    property var selectedMeals: []
    ListModel { id: members }
    function resizeMembers(size) {
        while (members.count < size) members.append({name: "", intolerances: ""});
        while (members.count > size) members.remove(members.count - 1);
    }
    function save() {
        const profiles = [];
        for (let i = 0; i < members.count; ++i)
            profiles.push({name: members.get(i).name, intolerances: members.get(i).intolerances});
        if (store.addGuestGroup(groupName.text, selectedMeals, profiles)) close();
    }
    onOpened: {
        selectedMeals = [];
        groupName.text = "";
        members.clear();
        count.value = 2;
        resizeMembers(count.value);
    }
    contentItem: ColumnLayout {
        spacing: 16
        ScrollView {
            id: editor
            Layout.fillWidth: true
            Layout.preferredHeight: Math.min(420, dialog.parent.height - 250)
            contentWidth: availableWidth
            clip: true
            ColumnLayout {
                width: editor.availableWidth
                spacing: 12
                Field {
                    id: groupName
                    objectName: "guestGroupName"
                    Layout.fillWidth: true
                    maximumLength: 100
                    placeholderText: I18n.tr("Nom du groupe (facultatif)")
                }
                Caption { text: I18n.tr("Sélectionnez les repas de présence") }
                Flow {
                    Layout.fillWidth: true
                    spacing: 6
                    Repeater {
                        model: Math.max(dialog.store.settings.count, dialog.store.meals.length)
                        delegate: Chip {
                            required property int index
                            objectName: "guestMeal-" + index
                            implicitWidth: Math.min(contentItem.implicitWidth + 30, editor.availableWidth)
                            contentItem: Text {
                                text: parent.text
                                font: parent.font
                                color: parent.checked ? Theme.accentDark : Theme.text
                                wrapMode: Text.WordWrap
                                verticalAlignment: Text.AlignVCenter
                            }
                            implicitHeight: Math.max(34, contentItem.implicitHeight + 16)
                            text: dialog.store.meals[index] ? dialog.store.meals[index].label + " · " + dialog.store.meals[index].title : I18n.tr("Repas ") + (index + 1)
                            checked: dialog.selectedMeals.indexOf(index) >= 0
                            onClicked: {
                                dialog.selectedMeals = checked ? dialog.selectedMeals.filter(i => i !== index) : dialog.selectedMeals.concat([index]);
                            }
                        }
                    }
                }
                Caption { text: dialog.selectedMeals.length + I18n.tr(" repas sélectionné(s)") }
                Caption { text: I18n.tr("Personnes supplémentaires") }
                NumberPicker {
                    id: count
                    objectName: "guestPeople"
                    to: 12
                    onValueChanged: dialog.resizeMembers(value)
                }
                Repeater {
                    model: members
                    delegate: ColumnLayout {
                        id: profile
                        required property int index
                        required property string name
                        required property string intolerances
                        Layout.fillWidth: true
                        Caption { text: I18n.tr("Personne ") + (profile.index + 1) }
                        Field {
                            objectName: "guestName-" + profile.index
                            Layout.fillWidth: true
                            text: profile.name
                            placeholderText: I18n.tr("Nom")
                            maximumLength: 100
                            onTextEdited: members.setProperty(profile.index, "name", text)
                        }
                        Field {
                            objectName: "guestIntolerances-" + profile.index
                            Layout.fillWidth: true
                            text: profile.intolerances
                            maximumLength: 1000
                            placeholderText: I18n.tr("Intolérances et aliments à éviter (séparés par des virgules)")
                            onTextEdited: members.setProperty(profile.index, "intolerances", text)
                        }
                    }
                }
                Caption {
                    Layout.fillWidth: true
                    text: I18n.tr("Les préférences de ces invités et leurs portions s’appliquent uniquement aux repas sélectionnés. Les autres repas gardent les préférences du foyer.")
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
                objectName: "saveGuestGroup"
                text: I18n.tr("Ajouter les invités")
                enabled: dialog.selectedMeals.length > 0
                primary: true
                onClicked: dialog.save()
            }
        }
    }
}
