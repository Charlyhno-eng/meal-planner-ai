import QtQuick

Canvas {
    id: icon
    property string kind: "coordinator"
    property color ink: Theme.accent
    implicitWidth: 32
    implicitHeight: 32
    onKindChanged: requestPaint()
    onInkChanged: requestPaint()
    onWidthChanged: requestPaint()
    onHeightChanged: requestPaint()
    onPaint: {
        const ctx = getContext("2d");
        ctx.reset();
        ctx.scale(width / 32, height / 32);
        ctx.strokeStyle = ink;
        ctx.lineWidth = 1.8;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        function line(x1, y1, x2, y2) {
            ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
        }
        function circle(x, y, radius) {
            ctx.beginPath(); ctx.arc(x, y, radius, 0, Math.PI * 2); ctx.stroke();
        }
        if (kind === "coordinator") {
            [[7, 7], [25, 7], [7, 25], [25, 25]].forEach(point => {
                line(16, 16, point[0], point[1]); circle(point[0], point[1], 3);
            });
            ctx.fillStyle = Theme.surface;
            ctx.beginPath(); ctx.arc(16, 16, 5, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
        } else if (kind === "planning") {
            ctx.strokeRect(5, 7, 22, 21);
            line(5, 13, 27, 13); line(10, 4, 10, 10); line(22, 4, 22, 10);
            [10, 16, 22].forEach(x => [18, 23].forEach(y => circle(x, y, 0.7)));
        } else if (kind === "preferences") {
            ctx.beginPath(); ctx.moveTo(7, 25);
            ctx.bezierCurveTo(2, 11, 12, 4, 27, 5);
            ctx.bezierCurveTo(28, 19, 19, 29, 7, 25); ctx.stroke();
            line(5, 28, 22, 11); line(12, 21, 12, 14); line(16, 17, 22, 17);
        } else if (kind === "user") {
            circle(16, 10, 5);
            ctx.beginPath(); ctx.moveTo(6, 28);
            ctx.lineTo(6, 24); ctx.quadraticCurveTo(6, 19, 11, 18);
            ctx.quadraticCurveTo(16, 16, 21, 18); ctx.quadraticCurveTo(26, 19, 26, 24);
            ctx.lineTo(26, 28); ctx.stroke();
        } else if (kind === "groceries") {
            ctx.beginPath(); ctx.moveTo(4, 13); ctx.lineTo(8, 27);
            ctx.lineTo(24, 27); ctx.lineTo(28, 13); ctx.closePath(); ctx.stroke();
            line(2, 13, 30, 13); line(9, 13, 14, 5); line(23, 13, 18, 5);
            line(12, 18, 13, 23); line(20, 18, 19, 23);
        } else {
            ctx.beginPath(); ctx.moveTo(16, 3); ctx.lineTo(27, 7);
            ctx.lineTo(26, 18); ctx.quadraticCurveTo(25, 25, 16, 29);
            ctx.quadraticCurveTo(7, 25, 6, 18); ctx.lineTo(5, 7);
            ctx.closePath(); ctx.stroke();
            line(10, 16, 14, 20); line(14, 20, 22, 12);
        }
    }
}
