// Muttern: Schraubenmuttern schweben und drehen sich langsam
import QtQuick

Szene {
    id: s

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.c("grund") }
            GradientStop { position: 1.0; color: s.mix("grund", "flaeche", 0.9) }
        }
    }
    Repeater {
        model: 28
        Sechseck {
            id: m
            required property int index
            readonly property real r: s.zufall(index * 3 + 11)
            readonly property real tiefe: 0.35 + r * 0.65
            width: 50 + tiefe * 150; height: width
            loch: true
            breite: 1.5 + tiefe * 2.5
            linie: r > 0.8 ? s.c("akzent2", 0.75) : s.c("akzent", 0.25 + tiefe * 0.5)
            fuellung: s.c("flaeche", 0.35)
            readonly property real x0: s.zufall(index + 300) * (s.width + 200) - 100
            readonly property real y0: s.zufall(index + 600) * (s.height + 200) - 100
            property real dy: 0
            x: x0
            y: y0 + dy
            RotationAnimation on rotation {
                from: 0; to: m.r > 0.5 ? 360 : -360
                duration: (40000 + m.r * 50000) / s.tempo
                loops: Animation.Infinite; paused: !s.laeuft
            }
            SequentialAnimation on dy {
                loops: Animation.Infinite; paused: !s.laeuft
                NumberAnimation { to: -30 - m.tiefe * 40; duration: (6000 + m.r * 5000) / s.tempo; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0; duration: (6000 + m.r * 5000) / s.tempo; easing.type: Easing.InOutSine }
            }
        }
    }
}
