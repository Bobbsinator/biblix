// Weicher, runder Lichtfleck (Mitte hell, Rand ausgeblendet), Grundbaustein fuer Bokeh, Nebel & Co.
import QtQuick
import QtQuick.Shapes

Shape {
    id: licht
    property color farbe: "white"
    property real staerke: 0.35
    property real kern: 0.55   // bis hierhin fast volle Staerke
    width: 200; height: 200
    preferredRendererType: Shape.CurveRenderer
    ShapePath {
        strokeWidth: -1
        fillGradient: RadialGradient {
            centerX: licht.width / 2; centerY: licht.height / 2
            centerRadius: licht.width / 2
            focalX: centerX; focalY: centerY
            GradientStop { position: 0.0; color: Qt.rgba(licht.farbe.r, licht.farbe.g, licht.farbe.b, licht.staerke) }
            GradientStop { position: licht.kern; color: Qt.rgba(licht.farbe.r, licht.farbe.g, licht.farbe.b, licht.staerke * 0.8) }
            GradientStop { position: 1.0; color: Qt.rgba(licht.farbe.r, licht.farbe.g, licht.farbe.b, 0) }
        }
        PathAngleArc {
            centerX: licht.width / 2; centerY: licht.height / 2
            radiusX: licht.width / 2; radiusY: licht.height / 2
            startAngle: 0; sweepAngle: 360
        }
    }
}
