// Sternenhimmel: funkelnde Sterne, ab und zu eine Sternschnuppe
import QtQuick

Szene {
    id: s

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.c("grund") }
            GradientStop { position: 0.75; color: s.mix("grund", "akzent", 0.10) }
            GradientStop { position: 1.0; color: s.mix("grund", "akzent", 0.22) }
        }
    }
    Repeater {
        model: 170
        Rectangle {
            id: stern
            required property int index
            readonly property real r: s.zufall(index)
            x: s.zufall(index + 500) * s.width
            y: s.zufall(index + 900) * s.height * 0.85
            width: 1.5 + r * 2.5; height: width; radius: width / 2
            color: r > 0.85 ? s.c("akzent2") : (r > 0.7 ? s.c("akzent") : s.c("text"))
            opacity: 0.6
            SequentialAnimation on opacity {
                loops: Animation.Infinite; paused: !s.laeuft
                NumberAnimation { to: 0.15; duration: 1200 + stern.r * 2600; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0.95; duration: 1200 + stern.r * 2600; easing.type: Easing.InOutSine }
            }
        }
    }
    // Sternschnuppe
    Item {
        id: schnuppe
        width: 220; height: 2
        rotation: 24
        opacity: 0
        Rectangle {
            anchors.fill: parent; radius: 1
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: s.c("text", 0.0) }
                GradientStop { position: 1.0; color: s.c("text", 0.95) }
            }
        }
        SequentialAnimation {
            running: true; loops: Animation.Infinite; paused: !s.laeuft
            PauseAnimation { duration: 6500 / s.tempo }
            ScriptAction {
                script: {
                    schnuppe.x = Math.random() * s.width * 0.7;
                    schnuppe.y = Math.random() * s.height * 0.35;
                }
            }
            ParallelAnimation {
                NumberAnimation { target: schnuppe; property: "x"; to: schnuppe.x + 520; duration: 900 }
                NumberAnimation { target: schnuppe; property: "y"; to: schnuppe.y + 230; duration: 900 }
                SequentialAnimation {
                    NumberAnimation { target: schnuppe; property: "opacity"; to: 1; duration: 150 }
                    NumberAnimation { target: schnuppe; property: "opacity"; to: 0; duration: 750 }
                }
            }
        }
    }
}
