// Lächelbögen (Bibi Mac): Bögen schwingen und lächeln im Takt
import QtQuick
import QtQuick.Shapes

Szene {
    id: s

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.c("grund") }
            GradientStop { position: 1.0; color: s.mix("grund", "akzent", 0.15) }
        }
    }
    Repeater {
        model: 9
        Shape {
            id: bogen
            required property int index
            readonly property real rad: Math.min(s.width, s.height) * (0.12 + index * 0.075)
            x: s.width / 2 - rad; y: s.height * 0.42 - rad
            width: rad * 2; height: rad * 2
            preferredRendererType: Shape.CurveRenderer
            property real schwung: 0
            rotation: schwung
            ShapePath {
                strokeColor: bogen.index % 3 === 0 ? s.c("akzent2") : s.c("akzent", 0.45 + bogen.index * 0.05)
                strokeWidth: 10 - bogen.index * 0.6; fillColor: "transparent"; capStyle: ShapePath.RoundCap
                PathAngleArc {
                    centerX: bogen.rad; centerY: bogen.rad; radiusX: bogen.rad; radiusY: bogen.rad
                    startAngle: 20; sweepAngle: 140
                }
            }
            SequentialAnimation on schwung {
                loops: Animation.Infinite; paused: !s.laeuft
                PauseAnimation { duration: bogen.index * 120 }
                NumberAnimation { to: 8; duration: 1800 / s.tempo; easing.type: Easing.InOutSine }
                NumberAnimation { to: -8; duration: 3600 / s.tempo; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0; duration: 1800 / s.tempo; easing.type: Easing.InOutSine }
            }
        }
    }
    // Zwei Augen-Punkte
    Repeater {
        model: 2
        Rectangle {
            required property int index
            readonly property real g: Math.min(s.width, s.height) * 0.045
            width: g; height: g; radius: g / 2
            x: s.width / 2 + (index ? 1 : -1) * Math.min(s.width, s.height) * 0.12 - g / 2
            y: s.height * 0.3
            color: s.c("akzent2")
            SequentialAnimation on height {
                loops: Animation.Infinite; paused: !s.laeuft
                PauseAnimation { duration: 4200 }
                NumberAnimation { to: 3; duration: 90 }
                NumberAnimation { to: Math.min(s.width, s.height) * 0.045; duration: 120 }
            }
        }
    }
}
