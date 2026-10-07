import QtQuick

Rectangle {
    color: Theme.surface
    radius: 16
    border.color: Theme.border
    border.width: 1
    Behavior on border.color {
        ColorAnimation { duration: Theme.motionDuration }
    }
}
