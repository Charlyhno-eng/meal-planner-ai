import QtQuick

// A single stroke style for navigation and household actions, independent of fonts.
Canvas {
    id: icon
    property string name: "meal"
    property color color: Theme.accent
    implicitWidth: 24
    implicitHeight: 24
    onNameChanged: requestPaint()
    onColorChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        ctx.scale(width / 24, height / 24);
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.6;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        function path(points) {
            ctx.beginPath();
            ctx.moveTo(points[0][0], points[0][1]);
            for (let i = 1; i < points.length; i++)
                ctx.lineTo(points[i][0], points[i][1]);
            ctx.stroke();
        }
        function circle(x, y, radius) {
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.stroke();
        }
        if (name === "microphone") {
            ctx.beginPath();
            ctx.arc(12, 6, 3, Math.PI, 0);
            ctx.lineTo(15, 12);
            ctx.arc(12, 12, 3, 0, Math.PI);
            ctx.closePath();
            ctx.stroke();
            ctx.beginPath();
            ctx.arc(12, 12, 6, 0, Math.PI);
            ctx.stroke();
            path([[12, 18], [12, 22]]);
            path([[8, 22], [16, 22]]);
        } else if (name === "assistant") {
            path([[12, 3], [14.5, 9.5], [21, 12], [14.5, 14.5], [12, 21], [9.5, 14.5], [3, 12], [9.5, 9.5], [12, 3]]);
            path([[20, 2], [20, 6]]);
            path([[18, 4], [22, 4]]);
        } else if (name === "planning") {
            ctx.strokeRect(4, 5, 16, 16);
            path([[4, 10], [20, 10]]);
            path([[8, 3], [8, 7]]);
            path([[16, 3], [16, 7]]);
            path([[8, 14], [11, 14]]);
            path([[14, 14], [16, 14]]);
            path([[8, 17], [11, 17]]);
        } else if (name === "pantry") {
            path([[7, 3], [17, 3], [17, 6], [7, 6], [7, 3]]);
            path([[7, 6], [5, 9], [5, 20], [19, 20], [19, 9], [17, 6]]);
            path([[5, 11], [19, 11]]);
            path([[9, 15], [15, 15]]);
        } else if (name === "groceries") {
            path([[3, 9], [21, 9], [18, 21], [6, 21], [3, 9]]);
            path([[7, 9], [10, 3]]);
            path([[17, 9], [14, 3]]);
            path([[9, 13], [10, 17]]);
            path([[15, 13], [14, 17]]);
        } else if (name === "household") {
            path([[3, 11], [12, 3], [21, 11]]);
            path([[5, 10], [5, 21], [19, 21], [19, 10]]);
            path([[10, 21], [10, 15], [14, 15], [14, 21]]);
        } else if (name === "settings") {
            circle(12, 12, 6);
            circle(12, 12, 2);
            for (let i = 0; i < 8; i++) {
                const angle = i * Math.PI / 4;
                path([[12 + Math.cos(angle) * 7, 12 + Math.sin(angle) * 7], [12 + Math.cos(angle) * 9, 12 + Math.sin(angle) * 9]]);
            }
        } else if (name === "agents") {
            circle(12, 5, 3);
            circle(5, 18, 3);
            circle(19, 18, 3);
            path([[10.5, 8], [6.5, 15]]);
            path([[13.5, 8], [17.5, 15]]);
            path([[8, 18], [16, 18]]);
        } else {
            circle(12, 12, 7);
            circle(12, 12, 4.5);
            path([[2, 4], [2, 20]]);
            path([[22, 4], [22, 20]]);
        }
    }
}
