import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "components"
import "pages"

ApplicationWindow {
    id: window
    objectName: "mainWindow"
    // Explicit property injection keeps the preview independently testable.
    required property var demo
    property int currentPage: 5
    property bool sidebarCollapsed: false
    Connections {
        target: window.demo.assistant
        function onModelSetupRequested() { window.currentPage = 4; }
    }
    onCurrentPageChanged: if (currentPage !== 5)
        demo.assistant.cancelDictation()
    property var pageTitles: [I18n.tr("Mes repas"), I18n.tr("Ma réserve"), I18n.tr("Mes courses"), I18n.tr("Mon foyer"), I18n.tr("Paramètres"), I18n.tr("Planifier avec l’IA"), I18n.tr("Interactions IA")]
    Binding {
        target: I18n
        property: "translator"
        value: window.demo
    }
    width: 1280
    height: 880
    minimumWidth: 960
    minimumHeight: 700
    visible: true
    title: "Meal Planner AI"
    color: Theme.background
    font.family: "DejaVu Sans"
    font.pixelSize: 14
    palette.window: Theme.background
    palette.windowText: Theme.text
    palette.text: Theme.text
    palette.base: Theme.background
    palette.button: Theme.surface
    palette.buttonText: Theme.text
    palette.highlight: Theme.accent
    palette.highlightedText: Theme.accentDark

    Rectangle {
        id: sidebar
        objectName: "sidebar"
        width: window.sidebarCollapsed ? 72 : window.width < 1100 ? 208 : 232
        clip: true
        Behavior on width {
            NumberAnimation {
                duration: Theme.motionDuration
                easing.type: Easing.OutCubic
            }
        }
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        color: Theme.sidebar
        Rectangle {
            anchors.right: parent.right
            height: parent.height
            width: 1
            color: Theme.border
            opacity: 0.5
        }
        ColumnLayout {
            anchors.fill: parent
            anchors.margins: window.sidebarCollapsed ? 12 : 18
            spacing: 8
            Item {
                Layout.fillWidth: true
                implicitHeight: 32
                Button {
                    objectName: "sidebarToggle"
                    anchors.right: parent.right
                    width: 32
                    height: 32
                    hoverEnabled: true
                    text: window.sidebarCollapsed ? I18n.tr("Déplier le menu") : I18n.tr("Replier le menu")
                    Accessible.name: text
                    ToolTip.visible: hovered
                    ToolTip.text: text
                    onClicked: window.sidebarCollapsed = !window.sidebarCollapsed
                    background: Rectangle {
                        radius: 8
                        color: parent.hovered ? Theme.surface : "transparent"
                        border.color: parent.activeFocus ? Theme.accent : "transparent"
                    }
                    contentItem: AppIcon {
                        name: window.sidebarCollapsed ? "chevron-right" : "chevron-left"
                        color: Theme.muted
                    }
                }
            }
            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                Layout.bottomMargin: 16
                spacing: 10
                Rectangle {
                    width: 34
                    height: 34
                    radius: 11
                    color: Theme.accent
                    AppIcon {
                        anchors.centerIn: parent
                        name: "meal"
                        color: Theme.accentDark
                        width: 26
                        height: 26
                    }
                }
                ColumnLayout {
                    visible: !window.sidebarCollapsed
                    spacing: 3
                    Text {
                        text: "Meal Planner AI"
                        font.pixelSize: 14
                        font.weight: Font.DemiBold
                        color: Theme.text
                    }
                    Caption {
                        text: I18n.tr("Votre cuisine, connectée")
                        font.pixelSize: 10
                        color: Theme.secondary
                    }
                }
            }
            Caption {
                visible: !window.sidebarCollapsed
                text: I18n.tr("VOTRE QUOTIDIEN")
                font.pixelSize: 10
                font.letterSpacing: 1.2
                Layout.leftMargin: 10
                Layout.bottomMargin: 10
            }
            Repeater {
                model: [
                    { title: I18n.tr("Assistant IA"), icon: "assistant", page: 5, count: 0 },
                    { title: I18n.tr("Repas"), icon: "planning", page: 0, count: window.demo.meals.length },
                    { title: I18n.tr("Réserve"), icon: "pantry", page: 1, count: window.demo.pantry.length },
                    { title: I18n.tr("Courses"), icon: "groceries", page: 2,
                      count: window.demo.groceries.filter(item => !item.available && !item.checked).length },
                    { title: I18n.tr("Foyer"), icon: "household", page: 3, count: 0 }
                ]
                delegate: NavButton {
                    required property var modelData
                    objectName: "nav" + modelData.page
                    Layout.fillWidth: true
                    text: modelData.title
                    iconName: modelData.icon
                    count: modelData.count
                    collapsed: window.sidebarCollapsed
                    selected: window.currentPage === modelData.page
                    onClicked: window.currentPage = modelData.page
                }
            }
            Item {
                Layout.fillHeight: true
            }
            Rectangle {
                Layout.fillWidth: true
                Layout.bottomMargin: 8
                implicitHeight: 1
                color: Theme.border
                opacity: 0.5
            }
            NavButton {
                objectName: "nav6"
                Layout.fillWidth: true
                text: I18n.tr("Interactions IA")
                iconName: "agents"
                collapsed: window.sidebarCollapsed
                selected: window.currentPage === 6
                onClicked: window.currentPage = 6
            }
            NavButton {
                objectName: "nav4"
                Layout.fillWidth: true
                Layout.bottomMargin: 8
                text: I18n.tr("Paramètres")
                iconName: "settings"
                collapsed: window.sidebarCollapsed
                selected: window.currentPage === 4
                onClicked: window.currentPage = 4
            }
        }
    }
    ColumnLayout {
        anchors.left: sidebar.right
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.leftMargin: window.width < 1100 ? 26 : 36
        anchors.rightMargin: window.width < 1100 ? 26 : 36
        spacing: 0
        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 102
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 5
                Caption {
                    text: I18n.tr("REPAS & COURSES À LA MAISON")
                    color: Theme.secondary
                    font.pixelSize: 10
                    font.letterSpacing: 1.3
                }
                Heading {
                    text: window.pageTitles[window.currentPage]
                    font.pixelSize: 25
                    Layout.fillWidth: true
                }
            }
        }
        StackLayout {
            id: pages
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.bottomMargin: 24
            currentIndex: window.currentPage
            onCurrentIndexChanged: pageReveal.restart()
            NumberAnimation {
                id: pageReveal
                target: pages
                property: "opacity"
                from: 0.65
                to: 1
                duration: Theme.motionDuration
                easing.type: Easing.OutCubic
            }
            PlanningPage {
                store: window.demo
                onConfigureRequested: planningDialog.open()
                onRecipeRequested: mealId => recipeDialog.showRecipe(mealId)
                onGroceriesRequested: window.currentPage = 2
            }
            PantryPage {
                store: window.demo
                onFoodRequested: food => foodDialog.edit(food)
            }
            GroceryPage {
                store: window.demo
            }
            HouseholdPage {
                store: window.demo
                onPreferencesRequested: preferencesDialog.open()
                onGuestRequested: guestDialog.open()
            }
            SettingsPage {
                store: window.demo
            }
            AssistantPage {
                store: window.demo
                onPlanningRequested: window.currentPage = 0
                onPantryRequested: window.currentPage = 1
                onGroceriesRequested: window.currentPage = 2
            }
            AgentInteractionsPage {}
        }
    }
    Shortcut {
        sequence: "Ctrl+7"
        onActivated: window.currentPage = 6
    }
    Shortcut {
        sequence: "Ctrl+6"
        onActivated: window.currentPage = 4
    }
    Shortcut {
        sequence: "Ctrl+1"
        onActivated: window.currentPage = 5
    }
    PlanningDialog {
        id: planningDialog
        objectName: "planningDialog"
        store: window.demo
    }
    PreferencesDialog {
        id: preferencesDialog
        objectName: "preferencesDialog"
        store: window.demo
    }
    FoodDialog {
        id: foodDialog
        objectName: "foodDialog"
        store: window.demo
    }
    GuestDialog {
        id: guestDialog
        objectName: "guestDialog"
        store: window.demo
    }
    RecipeDialog {
        id: recipeDialog
        objectName: "recipeDialog"
        store: window.demo
    }

    Connections {
        target: window.demo
        function onNotice(message) {
            toast.message = message;
            toast.open();
            toastTimer.restart();
        }
    }
    Popup {
        id: toast
        property string message: ""
        parent: Overlay.overlay
        x: Math.round((parent.width - width) / 2)
        y: parent.height - height - 28
        width: Math.min(implicitWidth, parent.width - 40)
        padding: 16
        closePolicy: Popup.NoAutoClose
        background: Rectangle {
            color: Theme.raised
            radius: 12
            border.color: Theme.accent
        }
        contentItem: Text {
            text: toast.message
            color: Theme.text
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            Accessible.role: Accessible.AlertMessage
            Accessible.name: text
        }
    }
    Timer {
        id: toastTimer
        interval: 3500
        onTriggered: toast.close()
    }
    Shortcut {
        sequence: "Ctrl+2"
        onActivated: window.currentPage = 0
    }
    Shortcut {
        sequence: "Ctrl+3"
        onActivated: window.currentPage = 1
    }
    Shortcut {
        sequence: "Ctrl+4"
        onActivated: window.currentPage = 2
    }
    Shortcut {
        sequence: "Ctrl+5"
        onActivated: window.currentPage = 3
    }
}
