// Tower bei Nacht (Bibi Tech): Fenster gehen an und aus, oben blinkt das Leuchtfeuer
import QtQuick
import QtQuick.Shapes

Szene {
    id: s

    readonly property real boden: s.height * 0.86
    readonly property real tb: Math.min(s.width * 0.11, 210)      // Turmbreite
    readonly property real th: s.height * 0.62                      // Turmhoehe
    readonly property real tx: (s.width - tb) / 2

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.c("grund") }
            GradientStop { position: 0.8; color: s.mix("grund", "akzent", 0.14) }
            GradientStop { position: 1.0; color: s.mix("grund", "akzent", 0.22) }
        }
    }
    // Sterne
    Repeater {
        model: 90
        Rectangle {
            required property int index
            readonly property real r: s.zufall(index + 1000)
            x: s.zufall(index + 1100) * s.width; y: s.zufall(index + 1200) * s.height * 0.6
            width: 1.5 + r * 1.5; height: width; radius: width / 2
            color: s.c("text")
            SequentialAnimation on opacity {
                loops: Animation.Infinite; paused: !s.laeuft
                NumberAnimation { to: 0.15; duration: 1500 + parent.r * 3000; easing.type: Easing.InOutSine }
                NumberAnimation { to: 0.8; duration: 1500 + parent.r * 3000; easing.type: Easing.InOutSine }
            }
        }
    }
    // Skyline links und rechts
    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            fillColor: s.mix("grund", "flaeche", 0.6); strokeColor: "transparent"
            PathSvg {
                path: {
                    let p = "M 0 " + s.boden, x = 0, i = 0;
                    while (x < s.width) {
                        const b = 40 + s.zufall(i + 50) * 90, h = s.height * (0.06 + s.zufall(i + 70) * 0.16);
                        if (Math.abs(x + b / 2 - s.width / 2) > s.tb * 1.2)
                            p += " L " + x + " " + (s.boden - h) + " L " + (x + b) + " " + (s.boden - h);
                        else
                            p += " L " + x + " " + s.boden + " L " + (x + b) + " " + s.boden;
                        x += b; i++;
                    }
                    return p + " L " + s.width + " " + s.height + " L 0 " + s.height + " Z";
                }
            }
        }
    }
    // Turm mit Spitze
    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            fillGradient: LinearGradient {
                x1: s.tx; y1: 0; x2: s.tx + s.tb; y2: 0
                GradientStop { position: 0.0; color: s.mix("flaeche", "akzent", 0.12) }
                GradientStop { position: 1.0; color: s.c("flaeche") }
            }
            strokeColor: s.c("akzent", 0.8); strokeWidth: 2
            startX: s.tx; startY: s.boden
            PathLine { x: s.tx; y: s.boden - s.th }
            PathLine { x: s.tx + s.tb * 0.2; y: s.boden - s.th - s.tb * 0.6 }
            PathLine { x: s.tx + s.tb * 0.8; y: s.boden - s.th - s.tb * 0.6 }
            PathLine { x: s.tx + s.tb; y: s.boden - s.th }
            PathLine { x: s.tx + s.tb; y: s.boden }
            PathLine { x: s.tx; y: s.boden }
        }
        ShapePath {
            strokeColor: s.c("akzent", 0.9); strokeWidth: 2.5; fillColor: "transparent"
            startX: s.tx + s.tb / 2; startY: s.boden - s.th - s.tb * 0.6
            PathLine { x: s.tx + s.tb / 2; y: s.boden - s.th - s.tb * 1.25 }
        }
    }
    // Fenster
    Grid {
        id: fenster
        x: s.tx + s.tb * 0.12; y: s.boden - s.th + s.tb * 0.15
        columns: 6; rowSpacing: s.th / 70; columnSpacing: s.tb * 0.06
        readonly property real fw: (s.tb * 0.76 - 5 * columnSpacing) / 6
        Repeater {
            id: fensterListe
            model: 6 * 52
            Rectangle {
                required property int index
                width: fenster.fw; height: s.th / 70 * 0.9
                color: s.zufall(index + 3) > 0.62 ? s.c("akzent2", 0.85) : s.c("akzent", 0.18)
            }
        }
    }
    // Zufaellige Fenster schalten (ein Timer fuer alle, schont die CPU)
    Timer {
        interval: 260 / s.tempo; repeat: true; running: s.laeuft
        onTriggered: {
            const f = fensterListe.itemAt(Math.floor(Math.random() * fensterListe.count));
            if (f) f.color = Math.random() > 0.5 ? s.c("akzent2", 0.85) : s.c("akzent", 0.18);
        }
    }
    // Leuchtfeuer
    Item {
        x: s.tx + s.tb / 2; y: s.boden - s.th - s.tb * 1.25
        Licht {
            id: feuer
            anchors.centerIn: parent; width: 160; height: 160
            farbe: s.c("akzent2"); staerke: 0.85; kern: 0.12
            SequentialAnimation on opacity {
                loops: Animation.Infinite; paused: !s.laeuft
                NumberAnimation { to: 1; duration: 180 }
                NumberAnimation { to: 0.15; duration: 1100; easing.type: Easing.OutQuad }
                PauseAnimation { duration: 600 }
            }
        }
        Rectangle { anchors.centerIn: parent; width: 8; height: 8; radius: 4; color: s.c("akzent2") }
    }
    // Boden
    Rectangle { y: s.boden; width: s.width; height: s.height - s.boden; color: s.mix("grund", "flaeche", 0.4) }
}
