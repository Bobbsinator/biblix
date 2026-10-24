// Synthwave: Retro-Sonne über einem endlosen Gitterboden
import QtQuick
import QtQuick.Shapes

Szene {
    id: s

    readonly property real horizont: s.height * 0.58
    // Himmel
    Rectangle {
        width: s.width; height: s.horizont
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.c("grund") }
            GradientStop { position: 1.0; color: s.mix("grund", "akzent", 0.35) }
        }
    }
    // Sonne mit Streifen
    Item {
        id: sonne
        width: Math.min(s.width, s.height) * 0.42; height: width
        x: (s.width - width) / 2; y: s.horizont - height * 0.78
        Licht { anchors.centerIn: parent; width: parent.width * 1.9; height: width; farbe: s.c("akzent2"); staerke: 0.22; kern: 0.2 }
        Rectangle {
            id: scheibe
            anchors.fill: parent; radius: width / 2
            gradient: Gradient {
                GradientStop { position: 0.0; color: s.c("akzent2") }
                GradientStop { position: 1.0; color: s.mix("akzent2", "akzent", 0.85) }
            }
        }
        Repeater {
            model: 6
            Rectangle {
                required property int index
                width: sonne.width; color: s.mix("grund", "akzent", 0.35)
                height: 3 + index * 2.4
                y: sonne.height * (0.52 + index * 0.08)
                SequentialAnimation on y {
                    loops: Animation.Infinite; paused: !s.laeuft
                    NumberAnimation { to: sonne.height * (0.55 + index * 0.08); duration: 2400 / s.tempo; easing.type: Easing.InOutSine }
                    NumberAnimation { to: sonne.height * (0.52 + index * 0.08); duration: 2400 / s.tempo; easing.type: Easing.InOutSine }
                }
            }
        }
    }
    // Boden
    Rectangle {
        y: s.horizont; width: s.width; height: s.height - s.horizont
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.mix("grund", "akzent", 0.25) }
            GradientStop { position: 1.0; color: s.c("grund") }
        }
    }
    // Gitter: Laengslinien laufen zum Fluchtpunkt, Querlinien kommen auf dich zu
    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: s.c("akzent", 0.7); strokeWidth: 1.5; fillColor: "transparent"
            PathSvg {
                path: {
                    let p = "";
                    const n = 26, mx = s.width / 2;
                    for (let i = -n; i <= n; i++)
                        p += "M " + (mx + i * 12) + " " + s.horizont + " L " + (mx + i * s.width / 9) + " " + s.height + " ";
                    return p;
                }
            }
        }
    }
    Repeater {
        model: 12
        Rectangle {
            id: quer
            required property int index
            property real t: 0
            // perspektivisch: nah am Horizont dicht, vorne weit auseinander
            y: s.horizont + Math.pow((index + t) / 12, 2.2) * (s.height - s.horizont)
            width: s.width; height: 1 + Math.pow((index + t) / 12, 2) * 2.5
            color: s.c("akzent", 0.3 + 0.5 * (index + t) / 12)
            NumberAnimation on t { from: 0; to: 1; duration: 1600 / s.tempo; loops: Animation.Infinite; paused: !s.laeuft }
        }
    }
}
