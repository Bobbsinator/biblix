// Tropfen: Ringe breiten sich auf einer ruhigen Fläche aus
import QtQuick

Szene {
    id: s

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.mix("grund", "akzent", 0.08) }
            GradientStop { position: 1.0; color: s.c("grund") }
        }
    }
    Repeater {
        model: 9
        Item {
            id: tropfen
            required property int index
            property real t: 0
            width: 1; height: 1
            Repeater {
                model: 3
                Rectangle {
                    required property int index
                    readonly property real tt: Math.max(0, tropfen.t - index * 0.12)
                    width: 30 + tt * 520; height: width * 0.42
                    x: -width / 2; y: -height / 2
                    radius: height / 2
                    color: "transparent"
                    border.width: 2.5 - index * 0.6
                    border.color: tropfen.index % 3 === 0 ? s.c("akzent2") : s.c("akzent")
                    opacity: tt > 0 ? (1 - tt) * 0.8 : 0
                }
            }
            SequentialAnimation {
                running: true; loops: Animation.Infinite; paused: !s.laeuft
                PauseAnimation { duration: (tropfen.index * 900 + 300) / s.tempo }
                ScriptAction {
                    script: {
                        tropfen.x = (0.08 + Math.random() * 0.84) * s.width;
                        tropfen.y = (0.15 + Math.random() * 0.75) * s.height;
                    }
                }
                NumberAnimation { target: tropfen; property: "t"; from: 0; to: 1; duration: 5200 / s.tempo; easing.type: Easing.OutCubic }
                PauseAnimation { duration: (2500 + tropfen.index * 400) / s.tempo }
            }
        }
    }
}
