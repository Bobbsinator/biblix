// Bauplan: technische Zeichnung einer Schraubenmutter wird Linie für Linie gezeichnet
import QtQuick
import QtQuick.Shapes

Szene {
    id: s

    readonly property real g: Math.min(s.width, s.height) * 0.5
    property real fortschritt: 0
    Rectangle { anchors.fill: parent; color: s.mix("grund", "akzent", 0.12) }
    // Millimeterpapier
    Shape {
        anchors.fill: parent
        ShapePath {
            strokeColor: s.c("akzent", 0.12); strokeWidth: 1; fillColor: "transparent"
            PathSvg {
                path: {
                    let p = "";
                    for (let x = 0; x < s.width; x += 24) p += "M " + x + " 0 L " + x + " " + s.height + " ";
                    for (let y = 0; y < s.height; y += 24) p += "M 0 " + y + " L " + s.width + " " + y + " ";
                    return p;
                }
            }
        }
        ShapePath {
            strokeColor: s.c("akzent", 0.22); strokeWidth: 1; fillColor: "transparent"
            PathSvg {
                path: {
                    let p = "";
                    for (let x = 0; x < s.width; x += 120) p += "M " + x + " 0 L " + x + " " + s.height + " ";
                    for (let y = 0; y < s.height; y += 120) p += "M 0 " + y + " L " + s.width + " " + y + " ";
                    return p;
                }
            }
        }
    }
    // Zeichnung: Mutter von oben, mit Bemassung; wird ueber die Strichlaenge aufgebaut
    Sechseck {
        anchors.centerIn: parent
        width: s.g; height: s.g; loch: true; breite: 3
        linie: s.c("text", 0.9)
        opacity: Math.min(1, s.fortschritt * 2)
        scale: 0.9 + 0.1 * Math.min(1, s.fortschritt * 2)
    }
    Shape {
        anchors.fill: parent
        opacity: Math.max(0, s.fortschritt * 2 - 1)
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: s.c("akzent2"); strokeWidth: 1.5; fillColor: "transparent"
            strokeStyle: ShapePath.DashLine; dashPattern: [6, 4]
            PathSvg {
                path: {
                    const cx = s.width / 2, cy = s.height / 2, r = s.g / 2;
                    return "M " + (cx - r * 1.3) + " " + cy + " L " + (cx + r * 1.3) + " " + cy
                         + " M " + cx + " " + (cy - r * 1.3) + " L " + cx + " " + (cy + r * 1.3);
                }
            }
        }
        ShapePath {
            strokeColor: s.c("akzent2"); strokeWidth: 1.5; fillColor: "transparent"
            PathSvg {
                path: {
                    const cx = s.width / 2, cy = s.height / 2, r = s.g / 2 * 0.866;
                    const y = cy + s.g / 2 + 40;
                    return "M " + (cx - r) + " " + y + " L " + (cx + r) + " " + y
                         + " M " + (cx - r) + " " + (y - 10) + " L " + (cx - r) + " " + (y + 10)
                         + " M " + (cx + r) + " " + (y - 10) + " L " + (cx + r) + " " + (y + 10);
                }
            }
        }
    }
    Text {
        opacity: Math.max(0, s.fortschritt * 2 - 1)
        x: s.width / 2 - width / 2; y: s.height / 2 + s.g / 2 + 52
        font.family: "DejaVu Sans Mono"; font.pixelSize: 18
        color: s.c("akzent2"); text: "SW 24 · M16 · DIN 934"
    }
    Text {
        x: 40; y: s.height - 70
        font.family: "DejaVu Sans Mono"; font.pixelSize: 16
        color: s.c("text", 0.5); text: "BIBI TECH · KONSTRUKTION · BLATT 1/1"
    }
    // Zeichenstift-Linie
    Rectangle {
        x: 0; width: s.width; height: 2
        y: s.height * s.fortschritt
        color: s.c("akzent2", 0.8)
        visible: s.fortschritt < 0.98
    }
    SequentialAnimation on fortschritt {
        loops: Animation.Infinite; paused: !s.laeuft
        NumberAnimation { from: 0; to: 1; duration: 9000 / s.tempo; easing.type: Easing.InOutQuad }
        PauseAnimation { duration: 14000 / s.tempo }
        NumberAnimation { to: 0; duration: 1500 / s.tempo }
    }
}
