import QtQuick

// Decorative, local vector artwork: a plate, fresh leaves and a shopping basket.
Item {
    id: art
    implicitWidth: 210
    implicitHeight: 172
    Item {
        width: 210
        height: 172
        anchors.centerIn: parent
        scale: Math.min(art.width / width, art.height / height)
        Rectangle {
            x: 27
            y: 8
            width: 152
            height: 152
            radius: 76
            color: "transparent"
            border.color: Theme.accent
            opacity: 0.18
        }
        Rectangle {
            x: 14
            y: 42
            width: 180
            height: 104
            radius: 52
            rotation: -24
            color: "transparent"
            border.color: Theme.secondary
            opacity: 0.25
        }
        Rectangle {
            x: 49
            y: 36
            width: 110
            height: 110
            radius: 55
            color: "#20332d"
            border.color: "#8cab88"
            border.width: 2
            Rectangle {
                anchors.centerIn: parent
                width: 88
                height: 88
                radius: 44
                color: "#365243"
                border.color: "#668763"
            }
            Repeater {
                model: 5
                Rectangle {
                    required property int index
                    x: 32 + (index * 23) % 44
                    y: 25 + (index * 19) % 50
                    width: 18
                    height: 29
                    radius: 9
                    rotation: index * 62 - 35
                    color: index % 2 ? Theme.accent : "#85b38a"
                }
            }
            Repeater {
                model: 4
                Rectangle {
                    required property int index
                    x: 30 + (index * 17) % 53
                    y: 40 + (index * 27) % 45
                    width: 12
                    height: 12
                    radius: 6
                    color: "#dfa68b"
                }
            }
        }
        Rectangle {
            x: 147
            y: 111
            width: 56
            height: 52
            radius: 16
            color: Theme.background
            border.color: Theme.secondary
            AppIcon {
                anchors.centerIn: parent
                name: "groceries"
                color: Theme.secondary
                width: 30
                height: 30
            }
        }
        Rectangle {
            x: 10
            y: 14
            width: 44
            height: 42
            radius: 13
            color: Theme.accentDark
            border.color: "#5d7c5b"
            AppIcon {
                anchors.centerIn: parent
                name: "household"
                width: 24
                height: 24
            }
        }
        Rectangle {
            x: 172
            y: 27
            width: 6
            height: 6
            radius: 3
            color: Theme.accent
        }
        Rectangle {
            x: 20
            y: 124
            width: 4
            height: 4
            radius: 2
            color: Theme.secondary
        }
    }
}
