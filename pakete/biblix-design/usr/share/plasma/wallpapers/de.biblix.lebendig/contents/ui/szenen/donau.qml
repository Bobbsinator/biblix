// Donau-Abend (Nassmacher): Sonne über dem Wasser, glitzernde Wellenlinien
import QtQuick

Szene {
    id: s

    readonly property real wasser: s.height * 0.6
    Rectangle {
        width: s.width; height: s.wasser
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.c("grund") }
            GradientStop { position: 0.55; color: s.mix("grund", "akzent", 0.45) }
            GradientStop { position: 1.0; color: s.mix("akzent", "akzent2", 0.55) }
        }
    }
    Item {
        id: sonne
        width: Math.min(s.width, s.height) * 0.2; height: width
        x: s.width * 0.62; y: s.wasser - height * 0.62
        Licht { anchors.centerIn: parent; width: parent.width * 3.2; height: width; farbe: s.c("akzent2"); staerke: 0.35; kern: 0.12 }
        Rectangle { anchors.fill: parent; radius: width / 2; color: s.c("akzent2") }
        SequentialAnimation on y {
            loops: Animation.Infinite; paused: !s.laeuft
            NumberAnimation { to: s.wasser - sonne.height * 0.5; duration: 30000 / s.tempo; easing.type: Easing.InOutSine }
            NumberAnimation { to: s.wasser - sonne.height * 0.75; duration: 30000 / s.tempo; easing.type: Easing.InOutSine }
        }
    }
    Rectangle {
        y: s.wasser; width: s.width; height: s.height - s.wasser
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.mix("akzent", "grund", 0.55) }
            GradientStop { position: 1.0; color: s.c("grund") }
        }
    }
    // Wellenlinien
    Repeater {
        model: 34
        Rectangle {
            id: welle
            required property int index
            readonly property real t: index / 34
            readonly property real r: s.zufall(index + 9)
            y: s.wasser + 6 + Math.pow(t, 1.6) * (s.height - s.wasser - 10)
            height: 1 + t * 3; radius: height / 2
            width: s.width * (0.05 + r * 0.18) * (0.5 + t)
            color: s.c("text", 0.10 + 0.25 * (1 - t))
            property real x0: s.zufall(index + 30) * s.width
            x: x0
            SequentialAnimation on x {
                loops: Animation.Infinite; paused: !s.laeuft
                NumberAnimation { to: welle.x0 + 40 + welle.r * 60; duration: (3000 + welle.r * 3000) / s.tempo; easing.type: Easing.InOutSine }
                NumberAnimation { to: welle.x0; duration: (3000 + welle.r * 3000) / s.tempo; easing.type: Easing.InOutSine }
            }
        }
    }
    // Sonnenspiegelung: flackernde Lichtstreifen
    Repeater {
        model: 22
        Rectangle {
            id: glanz
            required property int index
            readonly property real t: index / 22
            x: sonne.x + sonne.width / 2 - width / 2 + (s.zufall(index) - 0.5) * 30
            y: s.wasser + 4 + Math.pow(t, 1.3) * (s.height - s.wasser) * 0.8
            width: sonne.width * (0.9 - t * 0.5) * (0.6 + s.zufall(index + 5) * 0.6); height: 2 + t * 3
            radius: height / 2
            color: s.c("akzent2")
            SequentialAnimation on opacity {
                loops: Animation.Infinite; paused: !s.laeuft
                NumberAnimation { to: 0.15; duration: 400 + s.zufall(glanz.index + 2) * 900 }
                NumberAnimation { to: 0.85 - glanz.t * 0.5; duration: 400 + s.zufall(glanz.index + 4) * 900 }
            }
        }
    }
}
