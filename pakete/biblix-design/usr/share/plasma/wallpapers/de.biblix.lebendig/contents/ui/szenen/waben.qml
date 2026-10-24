// Waben: Licht wandert hinter einem Wabengitter entlang
import QtQuick
import QtQuick.Shapes

Szene {
    id: s

    // Lichter hinter dem Gitter
    Repeater {
        model: 5
        Licht {
            id: l
            required property int index
            readonly property real r: s.zufall(index + 21)
            width: s.width * (0.35 + r * 0.25); height: width
            farbe: index % 2 === 0 ? s.c("akzent") : s.c("akzent2")
            staerke: index % 2 === 0 ? 0.55 : 0.35
            kern: 0.3
            property real t: r
            x: (Math.sin(t * Math.PI * 2) * 0.45 + 0.5) * s.width - width / 2
            y: (Math.cos(t * Math.PI * 2 * 0.7 + index) * 0.4 + 0.5) * s.height - height / 2
            NumberAnimation on t {
                from: l.r; to: l.r + 1
                duration: (50000 + l.r * 30000) / s.tempo
                loops: Animation.Infinite; paused: !s.laeuft
            }
        }
    }
    // Wabengitter: dicke Linien in Grundfarbe, die Lichter scheinen durch die Zellen
    Shape {
        id: gitter
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        readonly property real a: 46
        function wabenPfad() {
            const w = Math.sqrt(3) * a, p = [];
            for (let reihe = -1; reihe * a * 1.5 < height + a * 2; reihe++) {
                for (let sp = -1; sp * w < width + w; sp++) {
                    const cx = sp * w + (reihe % 2 ? w / 2 : 0), cy = reihe * a * 1.5;
                    let z = "";
                    for (let i = 0; i < 6; i++) {
                        const wi = Math.PI / 3 * i + Math.PI / 6;
                        z += (i === 0 ? "M" : "L") + (cx + a * Math.cos(wi)).toFixed(1) + " " + (cy + a * Math.sin(wi)).toFixed(1) + " ";
                    }
                    p.push(z + "Z");
                }
            }
            return p.join(" ");
        }
        ShapePath {
            strokeColor: s.c("grund"); strokeWidth: 9; fillColor: "transparent"
            joinStyle: ShapePath.RoundJoin
            PathSvg { path: gitter.width > 0 ? gitter.wabenPfad() : "" }
        }
        ShapePath {
            strokeColor: s.c("rand", 0.6); strokeWidth: 1; fillColor: "transparent"
            PathSvg { path: gitter.width > 0 ? gitter.wabenPfad() : "" }
        }
    }
    // Zellen dunkel abgetoent, damit es nicht blendet
    Rectangle { anchors.fill: parent; color: s.c("grund", 0.35) }
}
