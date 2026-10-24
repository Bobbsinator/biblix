// Wellen: mehrere Wellenschichten gleiten übereinander
import QtQuick
import QtQuick.Shapes

Szene {
    id: s

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.c("grund") }
            GradientStop { position: 1.0; color: s.mix("grund", "akzent", 0.18) }
        }
    }
    Repeater {
        model: 5
        Item {
            id: schicht
            required property int index
            readonly property real tief: index / 4          // 0 = hinten, 1 = vorne
            readonly property real hoehe: s.height * (0.10 + 0.04 * index)
            readonly property real wl: s.width / (1.2 + index * 0.35)   // Wellenlaenge
            y: s.height * (0.48 + 0.1 * index)
            width: s.width * 2 + wl; height: s.height
            property real verschub: 0
            x: -verschub
            NumberAnimation on verschub {
                from: 0; to: schicht.wl
                duration: (26000 - schicht.index * 3500) / s.tempo
                loops: Animation.Infinite; paused: !s.laeuft
            }
            Shape {
                anchors.fill: parent
                preferredRendererType: Shape.CurveRenderer
                ShapePath {
                    strokeColor: s.mix("akzent", "text", schicht.tief * 0.3, 0.35 + schicht.tief * 0.3)
                    strokeWidth: 2
                    fillGradient: LinearGradient {
                        x1: 0; y1: 0; x2: 0; y2: schicht.hoehe * 3
                        GradientStop { position: 0.0; color: s.mix("akzent", "grund", 0.55 - schicht.tief * 0.35, 0.35 + schicht.tief * 0.25) }
                        GradientStop { position: 1.0; color: s.c("grund", 0.95) }
                    }
                    PathSvg {
                        path: {
                            let p = "M 0 " + schicht.hoehe / 2;
                            const n = Math.ceil(schicht.width / schicht.wl) * 2;
                            for (let i = 0; i < n; i++) {
                                const x0 = i * schicht.wl / 2, sgn = i % 2 ? 1 : -1;
                                p += " Q " + (x0 + schicht.wl / 4) + " " + (schicht.hoehe / 2 + sgn * schicht.hoehe / 2)
                                   + " " + (x0 + schicht.wl / 2) + " " + schicht.hoehe / 2;
                            }
                            return p + " L " + schicht.width + " " + s.height + " L 0 " + s.height + " Z";
                        }
                    }
                }
            }
        }
    }
}
