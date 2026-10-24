// Tunnel: Sechsecke fliegen auf dich zu, wie ein Flug durch eine Schraubenmutter
import QtQuick

Szene {
    id: s

    Licht {
        anchors.centerIn: parent
        width: Math.min(s.width, s.height) * 0.9; height: width
        farbe: s.c("akzent"); staerke: 0.25; kern: 0.2
    }
    Item {
        id: mitte
        anchors.centerIn: parent
        width: 1; height: 1
        RotationAnimation on rotation {
            from: 0; to: 360; duration: 90000 / s.tempo
            loops: Animation.Infinite; paused: !s.laeuft
        }
        Repeater {
            model: 22
            Sechseck {
                id: ring
                required property int index
                property real t: 0
                readonly property real gross: Math.max(s.width, s.height) * 1.3
                width: gross; height: gross
                x: -gross / 2; y: -gross / 2
                scale: Math.pow(t, 1.7)
                rotation: index * 8
                breite: 5
                linie: index % 5 === 0 ? s.c("akzent2") : s.c("akzent", 0.85)
                opacity: t < 0.15 ? t / 0.15 : (t > 0.8 ? (1 - t) / 0.2 : 1)
                SequentialAnimation on t {
                    loops: 1; paused: !s.laeuft
                    PauseAnimation { duration: ring.index * 9000 / 22 / s.tempo }
                    NumberAnimation { from: 0; to: 1; duration: 9000 / s.tempo; loops: Animation.Infinite }
                }
            }
        }
    }
}
