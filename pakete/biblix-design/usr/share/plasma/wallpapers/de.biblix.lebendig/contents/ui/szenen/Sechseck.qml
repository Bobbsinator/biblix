// Sechseck (Schraubenmutter), optional mit Bohrung
import QtQuick
import QtQuick.Shapes

Shape {
    id: sx
    property color linie: "white"
    property color fuellung: "transparent"
    property real breite: 2
    property bool loch: false
    width: 100; height: 100
    preferredRendererType: Shape.CurveRenderer
    readonly property real rr: Math.min(width, height) / 2 - breite
    function ecken() {
        let p = "";
        for (let i = 0; i < 6; i++) {
            const a = Math.PI / 3 * i + Math.PI / 6;
            p += (i === 0 ? "M" : "L") + (width / 2 + rr * Math.cos(a)) + " " + (height / 2 + rr * Math.sin(a)) + " ";
        }
        return p + "Z";
    }
    ShapePath {
        strokeColor: sx.linie; strokeWidth: sx.breite; fillColor: sx.fuellung
        joinStyle: ShapePath.RoundJoin
        PathSvg { path: sx.ecken() }
    }
    ShapePath {
        strokeColor: sx.loch ? sx.linie : "transparent"; strokeWidth: sx.breite; fillColor: "transparent"
        PathAngleArc { centerX: sx.width / 2; centerY: sx.height / 2; radiusX: sx.rr * 0.45; radiusY: sx.rr * 0.45; sweepAngle: 360 }
    }
}
