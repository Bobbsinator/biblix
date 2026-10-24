// Zugriffsindex (Bibi Budget Bank): Kurve läuft durch ein Raster, unten ein Laufband
import QtQuick
import QtQuick.Shapes

Szene {
    id: s

    readonly property real breite: s.width * 2
    readonly property real mitte: s.height * 0.5
    // Zufallskurve, doppelt so breit wie der Bildschirm und nahtlos (Anfang = Ende)
    readonly property var punkte: {
        const n = 64, p = [];
        for (let i = 0; i <= n; i++) {
            const t = i / n * Math.PI * 4;
            p.push(Math.sin(t) * 0.18 + Math.sin(t * 2.7 + 1) * 0.08 + Math.sin(t * 6.3) * 0.04);
        }
        return p;
    }
    function kurve(fuellen) {
        const n = punkte.length - 1;
        let p = "M 0 " + (mitte - punkte[0] * s.height);
        for (let i = 1; i <= n; i++) p += " L " + (i / n * breite) + " " + (mitte - punkte[i] * s.height);
        return fuellen ? p + " L " + breite + " " + s.height + " L 0 " + s.height + " Z" : p;
    }

    Rectangle { anchors.fill: parent; color: s.c("grund") }
    // Raster
    Shape {
        anchors.fill: parent
        ShapePath {
            strokeColor: s.c("rand", 0.55); strokeWidth: 1; fillColor: "transparent"
            PathSvg {
                path: {
                    let p = "";
                    for (let x = 0; x < s.width; x += s.width / 16) p += "M " + x + " 0 L " + x + " " + s.height + " ";
                    for (let y = 0; y < s.height; y += s.height / 9) p += "M 0 " + y + " L " + s.width + " " + y + " ";
                    return p;
                }
            }
        }
    }
    Item {
        id: band
        width: s.breite; height: s.height
        property real verschub: 0
        x: -verschub
        NumberAnimation on verschub { from: 0; to: s.width; duration: 40000 / s.tempo; loops: Animation.Infinite; paused: !s.laeuft }
        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                strokeColor: "transparent"
                fillGradient: LinearGradient {
                    x1: 0; y1: s.mitte - s.height * 0.3; x2: 0; y2: s.height
                    GradientStop { position: 0.0; color: s.c("akzent2", 0.25) }
                    GradientStop { position: 1.0; color: s.c("akzent2", 0.0) }
                }
                PathSvg { path: s.kurve(true) }
            }
            ShapePath {
                strokeColor: s.c("akzent2"); strokeWidth: 3; fillColor: "transparent"
                joinStyle: ShapePath.RoundJoin
                PathSvg { path: s.kurve(false) }
            }
        }
    }
    // Laufband unten
    Rectangle {
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom; bottomMargin: s.height * 0.08 }
        height: s.height * 0.045; color: s.c("flaeche", 0.9)
        clip: true
        Text {
            id: ticker
            anchors.verticalCenter: parent.verticalCenter
            font.family: "DejaVu Sans Mono"; font.bold: true; font.pixelSize: parent.height * 0.55
            color: s.c("akzent2")
            text: "ZUGRIFF ▲ 2,4 %   ·   BIBI BUDGET BANK   ·   ZUGRIFF IST KEIN BESITZ.   ·   GRUNDBEDARF ▲ 0,0 %   ·   KNAPPHEIT ▲ 7,1 %   ·   "
            NumberAnimation on x { from: s.width; to: -ticker.width; duration: 30000 / s.tempo; loops: Animation.Infinite; paused: !s.laeuft }
        }
    }
}
