import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ActionButton {
    id: control
    objectName: "startDatePicker"
    property string iso: "2026-01-01"
    property date chosen: new Date(Number(iso.slice(0, 4)), Number(iso.slice(5, 7)) - 1, Number(
                                       iso.slice(8, 10)))
    property var displayLocale: Qt.locale(I18n.language === "en" ? "en_GB" : "fr_FR")
    text: displayLocale.toString(chosen, (I18n.language === "en" ? "dddd, d MMMM yyyy" :
                                                                   "dddd d MMMM yyyy")) + "   ▦"
    Accessible.name: I18n.tr("Choisir la date de début : ") + text
    onClicked: calendar.open()
    Popup {
        id: calendar
        objectName: "calendarPopup"
        y: control.height + 6
        width: Math.min(340, control.width)
        padding: 16
        modal: false
        focus: true
        property date monthDate: control.chosen
        onOpened: monthDate = control.chosen
        background: Rectangle {
            color: Theme.raised
            radius: 12
            border.color: Theme.border
        }
        contentItem: ColumnLayout {
            spacing: 10
            RowLayout {
                Layout.fillWidth: true
                ActionButton {
                    text: "‹"
                    quiet: true
                    Accessible.name: I18n.tr("Mois précédent")
                    onClicked: calendar.monthDate = new Date(calendar.monthDate.getFullYear(),
                                                             calendar.monthDate.getMonth() - 1, 1)
                }
                Text {
                    text: control.displayLocale.toString(calendar.monthDate, "MMMM yyyy")
                    color: Theme.text
                    font.pixelSize: 14
                    Layout.fillWidth: true
                    horizontalAlignment: Text.AlignHCenter
                }
                ActionButton {
                    text: "›"
                    quiet: true
                    Accessible.name: I18n.tr("Mois suivant")
                    onClicked: calendar.monthDate = new Date(calendar.monthDate.getFullYear(),
                                                             calendar.monthDate.getMonth() + 1, 1)
                }
            }
            DayOfWeekRow {
                Layout.fillWidth: true
                locale: control.displayLocale
                delegate: Text {
                    required property string shortName
                    text: shortName
                    font.pixelSize: 11
                    color: Theme.muted
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            MonthGrid {
                Layout.fillWidth: true
                Layout.preferredHeight: 224
                month: calendar.monthDate.getMonth()
                year: calendar.monthDate.getFullYear()
                locale: control.displayLocale
                delegate: Button {
                    id: day
                    required property var model
                    objectName: "calendarDay-" + Qt.formatDate(model.date, "yyyy-MM-dd")
                    text: model.day
                    Accessible.name: control.displayLocale.toString(model.date, (I18n.language
                                                                                 === "en"
                                                                                 ? "dddd, d MMMM yyyy" :
                                                                                   "dddd d MMMM yyyy"))
                    hoverEnabled: true
                    background: Rectangle {
                        radius: 8
                        color: Qt.formatDate(day.model.date, "yyyy-MM-dd") === control.iso
                               ? Theme.accent : day.hovered ? Theme.surface : "transparent"
                        border.color: day.activeFocus ? Theme.accent : "transparent"
                    }
                    contentItem: Text {
                        text: day.text
                        font.pixelSize: 12
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        color: Qt.formatDate(day.model.date, "yyyy-MM-dd") === control.iso
                               ? Theme.accentDark : day.model.month === calendar.monthDate.getMonth(
                                     ) ? Theme.text : Theme.muted
                    }
                    onClicked: {
                        control.iso = Qt.formatDate(model.date, "yyyy-MM-dd");
                        calendar.close();
                    }
                }
            }
            ActionButton {
                text: I18n.tr("Aujourd’hui")
                quiet: true
                Layout.fillWidth: true
                onClicked: {
                    control.iso = Qt.formatDate(new Date(), "yyyy-MM-dd");
                    calendar.close();
                }
            }
        }
    }
}
