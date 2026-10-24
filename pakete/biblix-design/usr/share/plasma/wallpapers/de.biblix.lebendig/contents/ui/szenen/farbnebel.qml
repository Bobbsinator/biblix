// Farbnebel: grosse weiche Farbwolken ziehen langsam und mischen sich
import QtQuick

Szene {
    id: s

    Repeater {
        model: 7
        Licht {
            id: w
            required property int index
            readonly property real r: s.zufall(index * 5 + 2)
            width: Math.max(s.width, s.height) * (0.55 + r * 0.45); height: width
            farbe: [s.c("akzent"), s.c("akzent2"), s.mix("akzent", "akzent2", 0.5), s.c("akzent"), s.c("rand"), s.c("akzent2"), s.c("text")][index]
            staerke: index === 6 ? 0.08 : 0.30
            kern: 0.15
            property real t: r
            x: (0.5 + 0.42 * Math.sin(t * Math.PI * 2 + index)) * s.width - width / 2
            y: (0.5 + 0.38 * Math.cos(t * Math.PI * 2 * (0.6 + r * 0.5) + index * 2)) * s.height - height / 2
            NumberAnimation on t {
                from: w.r; to: w.r + 1
                duration: (60000 + w.r * 40000) / s.tempo
                loops: Animation.Infinite; paused: !s.laeuft
            }
        }
    }
}
