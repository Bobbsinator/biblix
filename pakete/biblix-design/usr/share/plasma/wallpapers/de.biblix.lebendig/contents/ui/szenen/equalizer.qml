// Equalizer: Balken tanzen wie bei einer Musikanlage, mit Spiegelung
import QtQuick

Szene {
    id: s

    readonly property int anzahl: 48
    readonly property real breite: s.width / anzahl
    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.c("grund") }
            GradientStop { position: 0.7; color: s.mix("grund", "flaeche", 0.7) }
            GradientStop { position: 1.0; color: s.c("grund") }
        }
    }
    Repeater {
        model: s.anzahl
        Item {
            id: spalte
            required property int index
            readonly property real r: s.zufall(index + 7)
            x: index * s.breite
            width: s.breite; height: s.height
            property real pegel: 0.2
            readonly property real boden: s.height * 0.68
            // Balken
            Rectangle {
                x: s.breite * 0.15; width: s.breite * 0.7
                height: spalte.pegel * s.height * 0.5
                y: spalte.boden - height
                radius: 3
                gradient: Gradient {
                    GradientStop { position: 0.0; color: s.c("akzent2") }
                    GradientStop { position: 0.35; color: s.c("akzent") }
                    GradientStop { position: 1.0; color: s.mix("akzent", "grund", 0.5) }
                }
            }
            // Spiegelung
            Rectangle {
                x: s.breite * 0.15; width: s.breite * 0.7
                y: spalte.boden + 4
                height: spalte.pegel * s.height * 0.18
                radius: 3
                gradient: Gradient {
                    GradientStop { position: 0.0; color: s.c("akzent", 0.28) }
                    GradientStop { position: 1.0; color: s.c("akzent", 0.0) }
                }
            }
            SequentialAnimation on pegel {
                loops: Animation.Infinite; paused: !s.laeuft
                NumberAnimation {
                    to: 0.15 + s.zufall(spalte.index * 3) * 0.85 * (0.5 + 0.5 * Math.sin(spalte.index / s.anzahl * Math.PI))
                    duration: (300 + spalte.r * 500) / s.tempo; easing.type: Easing.OutQuad
                }
                NumberAnimation { to: 0.08 + spalte.r * 0.2; duration: (400 + spalte.r * 600) / s.tempo; easing.type: Easing.InQuad }
                NumberAnimation { to: 0.3 + s.zufall(spalte.index * 5) * 0.6; duration: (350 + spalte.r * 450) / s.tempo; easing.type: Easing.OutQuad }
                NumberAnimation { to: 0.1; duration: (500 + spalte.r * 500) / s.tempo; easing.type: Easing.InQuad }
            }
        }
    }
}
