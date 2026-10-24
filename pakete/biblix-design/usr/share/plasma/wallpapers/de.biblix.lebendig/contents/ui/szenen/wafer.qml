// Wafer (Bibi Tech): Silizium-Scheibe dreht sich, ein Laser tastet die Chips ab
import QtQuick
import QtQuick.Shapes

Szene {
    id: s

    readonly property real d: Math.min(s.width, s.height) * 0.82
    Rectangle { anchors.fill: parent; color: s.c("grund") }
    Licht { anchors.centerIn: parent; width: s.d * 1.5; height: width; farbe: s.c("akzent"); staerke: 0.18; kern: 0.3 }
    Item {
        id: scheibe
        anchors.centerIn: parent
        width: s.d; height: s.d
        RotationAnimation on rotation { from: 0; to: 360; duration: 120000 / s.tempo; loops: Animation.Infinite; paused: !s.laeuft }
        Rectangle {
            anchors.fill: parent; radius: width / 2
            gradient: Gradient {
                GradientStop { position: 0.0; color: s.mix("flaeche", "akzent", 0.35) }
                GradientStop { position: 0.5; color: s.mix("flaeche", "akzent2", 0.18) }
                GradientStop { position: 1.0; color: s.mix("flaeche", "akzent", 0.25) }
            }
            border.color: s.c("akzent", 0.7); border.width: 3
        }
        // Chip-Raster innerhalb des Kreises
        Shape {
            anchors.fill: parent
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                strokeColor: s.c("grund", 0.75); strokeWidth: 2; fillColor: "transparent"
                PathSvg {
                    path: {
                        const n = 14, g = s.d / n, r = s.d / 2 - 10;
                        let p = "";
                        for (let i = 0; i < n; i++)
                            for (let k = 0; k < n; k++) {
                                const x = i * g, y = k * g;
                                const ecken = [[x, y], [x + g, y], [x, y + g], [x + g, y + g]];
                                if (ecken.every(e => Math.hypot(e[0] - s.d / 2, e[1] - s.d / 2) < r))
                                    p += "M " + (x + 3) + " " + (y + 3) + " h " + (g - 6) + " v " + (g - 6) + " h " + (-(g - 6)) + " Z ";
                            }
                        return p;
                    }
                }
            }
        }
        // Kerbe
        Rectangle { x: s.d / 2 - 14; y: s.d - 10; width: 28; height: 14; radius: 7; color: s.c("grund") }
    }
    // Laser-Abtastlinie
    Rectangle {
        id: laser
        x: (s.width - s.d) / 2; width: s.d; height: 3
        color: s.c("akzent2")
        Licht { anchors.centerIn: parent; width: parent.width; height: 60; farbe: s.c("akzent2"); staerke: 0.3; kern: 0.05 }
        SequentialAnimation on y {
            loops: Animation.Infinite; paused: !s.laeuft
            NumberAnimation { from: (s.height - s.d) / 2; to: (s.height + s.d) / 2; duration: 7000 / s.tempo; easing.type: Easing.InOutSine }
            NumberAnimation { from: (s.height + s.d) / 2; to: (s.height - s.d) / 2; duration: 7000 / s.tempo; easing.type: Easing.InOutSine }
        }
    }
}
