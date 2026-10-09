pragma Singleton
import QtQuick

QtObject {
    readonly property color background: "#19262b"
    readonly property color sidebar: "#1f2d32"
    readonly property color surface: "#27373d"
    readonly property color raised: "#32474d"
    readonly property color border: "#40565c"
    readonly property color borderHover: "#718e85"
    readonly property color text: "#f0f2ec"
    readonly property color muted: "#a9b7b9"
    readonly property color accent: "#b7d99a"
    readonly property color accentDark: "#293c2c"
    readonly property color accentHover: "#c9e8b0"
    readonly property color secondary: "#94cec7"
    readonly property color selected: "#33493e"
    readonly property color hero: "#2d443d"
    property bool reducedMotion: false
    readonly property int motionDuration: reducedMotion ? 0 : 160
    readonly property color danger: "#f0b6a5"
}
