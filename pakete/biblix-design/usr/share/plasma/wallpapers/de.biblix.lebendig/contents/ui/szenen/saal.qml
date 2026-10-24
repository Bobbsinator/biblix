// Saallichter (Bibiplexx): Scheinwerfer schwenken, Staub tanzt im Licht, Reihe sieben leuchtet
import QtQuick
import QtQuick.Shapes
import QtQuick.Particles

Szene {
    id: s

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.mix("grund", "akzent", 0.1) }
            GradientStop { position: 1.0; color: s.c("grund") }
        }
    }
    // Leinwand oben
    Rectangle {
        x: s.width * 0.18; y: s.height * 0.08; width: s.width * 0.64; height: s.height * 0.3
        radius: 6
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.mix("flaeche", "akzent", 0.3) }
            GradientStop { position: 1.0; color: s.c("flaeche") }
        }
        border.color: s.c("akzent", 0.6); border.width: 2
        SequentialAnimation on opacity {
            loops: Animation.Infinite; paused: !s.laeuft
            NumberAnimation { to: 0.75; duration: 2300 }
            NumberAnimation { to: 1.0; duration: 1700 }
        }
    }
    // Scheinwerfer
    Repeater {
        model: 4
        Item {
            id: kegel
            required property int index
            x: s.width * (0.12 + index * 0.25); y: s.height
            Shape {
                id: strahl
                x: -s.width * 0.09; y: -s.height * 1.1
                width: s.width * 0.18; height: s.height * 1.1
                transformOrigin: Item.Bottom
                preferredRendererType: Shape.CurveRenderer
                ShapePath {
                    strokeColor: "transparent"
                    fillGradient: LinearGradient {
                        x1: 0; y1: strahl.height; x2: 0; y2: 0
                        GradientStop { position: 0.0; color: kegel.index % 2 ? s.c("akzent2", 0.35) : s.c("akzent", 0.35) }
                        GradientStop { position: 1.0; color: s.c("akzent", 0.0) }
                    }
                    startX: strahl.width / 2 - 6; startY: strahl.height
                    PathLine { x: 0; y: 0 }
                    PathLine { x: strahl.width; y: 0 }
                    PathLine { x: strahl.width / 2 + 6; y: strahl.height }
                }
                SequentialAnimation on rotation {
                    loops: Animation.Infinite; paused: !s.laeuft
                    NumberAnimation { from: -22 + kegel.index * 6; to: 22 - kegel.index * 4; duration: (5200 + kegel.index * 900) / s.tempo; easing.type: Easing.InOutSine }
                    NumberAnimation { from: 22 - kegel.index * 4; to: -22 + kegel.index * 6; duration: (5200 + kegel.index * 900) / s.tempo; easing.type: Easing.InOutSine }
                }
            }
        }
    }
    // Staub im Licht
    ParticleSystem { id: sys; anchors.fill: parent; paused: !s.laeuft }
    ImageParticle { system: sys; source: "qrc:///particleresources/glowdot.png"; color: s.c("text"); alpha: 0.35 }
    Emitter {
        system: sys; anchors.fill: parent
        emitRate: 14; lifeSpan: 9000; startTime: 9000
        size: 4; sizeVariation: 3
        velocity: PointDirection { xVariation: 6; yVariation: 6; y: -4 }
    }
    // Sitzreihen
    Repeater {
        model: 3
        Row {
            id: reihe
            required property int index
            spacing: 10
            x: (s.width - (16 * 46 + 15 * 10)) / 2 - index * 20
            y: s.height * (0.72 + index * 0.08)
            Repeater {
                model: 16
                Rectangle {
                    required property int index
                    width: 46 + reihe.index * 3; height: 30 + reihe.index * 3; radius: 8
                    color: reihe.index === 1 && index === 7 ? s.c("akzent2") : s.c("flaeche")
                    border.color: s.c("rand"); border.width: 1
                }
            }
        }
    }
}
