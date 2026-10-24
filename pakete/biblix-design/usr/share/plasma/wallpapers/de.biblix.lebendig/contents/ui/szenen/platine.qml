// Platine: Leiterbahnen, über die Stromimpulse flitzen
import QtQuick
import QtQuick.Shapes

Szene {
    id: s

    // Leiterbahnen: rechtwinklige Wege mit 45-Grad-Knick, einmal pro Groesse berechnet
    readonly property var bahnen: {
        const b = [], n = 34;
        if (s.width <= 0) return b;
        for (let i = 0; i < n; i++) {
            let x = Math.round(s.zufall(i + 1) * s.width / 24) * 24;
            let y = Math.round(s.zufall(i + 101) * s.height / 24) * 24;
            let p = "M " + x + " " + y;
            const schritte = 3 + Math.floor(s.zufall(i + 201) * 4);
            let richtung = Math.floor(s.zufall(i + 301) * 4);
            for (let k = 0; k < schritte; k++) {
                const l = (3 + Math.floor(s.zufall(i * 7 + k) * 9)) * 24;
                if (richtung % 2 === 0) x += (richtung === 0 ? l : -l); else y += (richtung === 1 ? l : -l);
                // 45-Grad-Ecke
                const d = 24;
                p += " L " + x + " " + y;
                richtung = (richtung + (s.zufall(i * 13 + k) > 0.5 ? 1 : 3)) % 4;
                if (richtung % 2 === 0) { x += (richtung === 0 ? d : -d); y += d; } else { y += (richtung === 1 ? d : -d); x += d; }
                p += " L " + x + " " + y;
            }
            b.push({ pfad: p, ex: x, ey: y });
        }
        return b;
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.mix("grund", "akzent", 0.05) }
            GradientStop { position: 1.0; color: s.c("grund") }
        }
    }
    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: s.c("rand"); strokeWidth: 3; fillColor: "transparent"
            joinStyle: ShapePath.RoundJoin; capStyle: ShapePath.RoundCap
            PathSvg { path: s.bahnen.map(b => b.pfad).join(" ") }
        }
    }
    // Loetpunkte an den Enden
    Repeater {
        model: s.bahnen.length
        Rectangle {
            required property int index
            readonly property var b: s.bahnen[index]
            width: 12; height: 12; radius: 6
            x: (b ? b.ex : 0) - 6; y: (b ? b.ey : 0) - 6
            color: s.c("grund"); border.width: 2; border.color: s.c("akzent", 0.6)
        }
    }
    // Impulse
    Repeater {
        model: s.bahnen.length
        Item {
            id: impuls
            required property int index
            width: 1; height: 1
            Licht { anchors.centerIn: parent; width: 34; height: 34; farbe: impuls.index % 4 ? s.c("akzent") : s.c("akzent2"); staerke: 0.9; kern: 0.15 }
            Rectangle { anchors.centerIn: parent; width: 5; height: 5; radius: 2.5; color: s.c("text") }
            PathAnimation {
                target: impuls; running: true; paused: !s.laeuft
                loops: Animation.Infinite
                duration: (2600 + s.zufall(impuls.index + 7) * 3200) / s.tempo
                path: Path { PathSvg { path: s.bahnen.length > impuls.index ? s.bahnen[impuls.index].pfad : "M 0 0" } }
            }
        }
    }
}
