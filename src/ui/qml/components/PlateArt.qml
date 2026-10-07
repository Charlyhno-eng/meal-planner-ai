import QtQuick

// Recipe-specific vector illustrations: no remote images or runtime assets.
Item {
    id: art
    property color tone: "#aabb88"
    property int variant: 0
    property int kind: Math.max(0, variant) % 7
    clip: true
    Rectangle {
        anchors.fill: parent
        color: art.tone
        opacity: 0.13
        radius: 10
    }
    Item {
        width: 146
        height: 146
        anchors.centerIn: parent
        scale: Math.min(1, (art.height - 12) / 146)
        Rectangle {
            x: 5
            y: 6
            width: 146
            height: 146
            radius: 73
            color: "#152426"
            opacity: 0.3
        }
        Rectangle {
            width: 146
            height: 146
            radius: 73
            color: "#d9ddd0"
            border.color: "#bcc7b9"
            border.width: 7
            Rectangle {
                anchors.centerIn: parent
                width: 112
                height: 112
                radius: 56
                color: "#c6cdbb"
                border.color: "#b9c4b0"
            }
            Rectangle {
                visible: art.kind === 2
                x: 28
                y: 28
                width: 92
                height: 88
                radius: 42
                color: "#c68f4e"
            }
            Repeater {
                model: art.kind === 1 || art.kind === 5 ? 28 : 16
                Rectangle {
                    required property int index
                    width: art.kind === 1 ? 27 : art.kind === 5 ? 6 : 18 + index % 3 * 4
                    height: art.kind === 1 ? 7 : art.kind === 5 ? 13 : 15 + index % 4 * 2
                    radius: art.kind === 5 ? 3 : 7
                    x: 29 + (index * 29 + art.kind * 7) % 65
                    y: 28 + index * 19 % 76
                    rotation: index * 41
                    color: art.kind === 1 ? (index % 5 ? "#dcca83" : "#728655") : art.kind === 5 ? (
                                                                                                       index % 6
                                                                                                       ? "#e5d7b4" :
                                                                                                         "#99866b") :
                                                                                                   art.kind
                                                                                                   === 2 ? (index
                                                                                                            % 4 ? "#e6c785" :
                                                                                                                  "#e9e4c9") :
                                                                                                           ["#6d8a58",
                                                                                                            "#dda573",
                                                                                                            "#c26750",
                                                                                                            "#e6cf95",
                                                                                                            "#89964c"][(
                                                                                                                           index + art.kind)
                                                                                                                       % 5]
                }
            }
            Rectangle {
                visible: art.kind === 4
                x: 43
                y: 41
                width: 61
                height: 51
                radius: 12
                rotation: -18
                color: "#d3947e"
                Repeater {
                    model: 4
                    Rectangle {
                        required property int index
                        x: 10 + index * 12
                        y: 6
                        width: 3
                        height: 39
                        radius: 2
                        color: "#efb59c"
                        rotation: 8
                    }
                }
            }
            Rectangle {
                visible: art.kind === 3
                x: 32
                y: 32
                width: 44
                height: 84
                radius: 17
                rotation: -25
                color: "#bf925c"
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: 5
                    radius: 12
                    color: "#879955"
                }
                Rectangle {
                    x: 4
                    y: 21
                    width: 36
                    height: 45
                    radius: 20
                    color: "#f1eada"
                    Rectangle {
                        anchors.centerIn: parent
                        width: 19
                        height: 19
                        radius: 10
                        color: "#d8ac4e"
                    }
                }
            }
            Repeater {
                model: art.kind === 6 ? 8 : 6
                Rectangle {
                    required property int index
                    width: art.kind === 6 ? 9 : 4
                    height: 9
                    radius: art.kind === 6 ? 2 : 3
                    x: 34 + index * 31 % 71
                    y: 32 + index * 23 % 73
                    color: art.kind === 6 ? "#f0ebd9" : "#dae2ba"
                    rotation: index * 33
                }
            }
        }
    }
}
