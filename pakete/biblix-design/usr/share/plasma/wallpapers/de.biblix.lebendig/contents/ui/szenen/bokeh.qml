// Bokeh: grosse, unscharfe Lichter treiben langsam vorbei
import QtQuick

Szene {
    id: s

    Repeater {
        model: 26
        Licht {
            id: l
            required property int index
            readonly property real r: s.zufall(index * 7 + 3)
            width: 120 + r * 320; height: width
            farbe: r > 0.66 ? s.c("akzent") : (r > 0.33 ? s.c("akzent2") : s.c("text"))
            staerke: r > 0.33 ? 0.22 : 0.10
            kern: 0.7
            readonly property real x0: s.zufall(index + 40) * s.width - width / 2
            readonly property real y0: s.zufall(index + 80) * s.height - height / 2
            property real dx: 0
            property real dy: 0
            x: x0 + dx
            y: y0 + dy
            SequentialAnimation on dx {
                loops: Animation.Infinite; paused: !s.laeuft
                NumberAnimation { to: 140 + l.r * 160; duration: (18000 + l.r * 14000) / s.tempo; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0; duration: (18000 + l.r * 14000) / s.tempo; easing.type: Easing.InOutSine }
            }
            SequentialAnimation on dy {
                loops: Animation.Infinite; paused: !s.laeuft
                NumberAnimation { to: -90 - l.r * 60; duration: (14000 + l.r * 9000) / s.tempo; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0; duration: (14000 + l.r * 9000) / s.tempo; easing.type: Easing.InOutSine }
            }
            SequentialAnimation on opacity {
                loops: Animation.Infinite; paused: !s.laeuft
                NumberAnimation { to: 0.35; duration: 7000 + l.r * 6000; easing.type: Easing.InOutSine }
                NumberAnimation { to: 1.0; duration: 7000 + l.r * 6000; easing.type: Easing.InOutSine }
            }
        }
    }
}
