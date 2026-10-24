// Route (Bibi Delivery): Stadtplan von oben, Lieferungen flitzen über die Straßen
import QtQuick
import QtQuick.Shapes

Szene {
    id: s

    readonly property real raster: Math.max(60, s.width / 22)
    readonly property var touren: {
        const t = [];
        if (s.width <= 0) return t;
        const sp = Math.floor(s.width / s.raster), ze = Math.floor(s.height / s.raster);
        for (let i = 0; i < 16; i++) {
            let x = Math.floor(s.zufall(i + 11) * sp), y = Math.floor(s.zufall(i + 22) * ze);
            let p = "M " + x * s.raster + " " + y * s.raster;
            for (let k = 0; k < 6; k++) {
                if ((i + k) % 2) x = Math.max(0, Math.min(sp, x + Math.round((s.zufall(i * 9 + k) - 0.5) * 8)));
                else y = Math.max(0, Math.min(ze, y + Math.round((s.zufall(i * 7 + k + 3) - 0.5) * 6)));
                p += " L " + x * s.raster + " " + y * s.raster;
            }
            t.push(p);
        }
        return t;
    }

    Rectangle { anchors.fill: parent; color: s.c("grund") }
    // Haeuserbloecke
    Repeater {
        model: Math.ceil(s.width / s.raster) * Math.ceil(s.height / s.raster)
        Rectangle {
            required property int index
            readonly property int sp: Math.ceil(s.width / s.raster)
            x: (index % sp) * s.raster + 6; y: Math.floor(index / sp) * s.raster + 6
            width: s.raster - 12; height: s.raster - 12; radius: 4
            color: s.zufall(index + 77) > 0.9 ? s.c("akzent", 0.12) : s.c("flaeche", 0.8)
        }
    }
    // Tourenlinien
    Shape {
        anchors.fill: parent
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: s.c("akzent", 0.22); strokeWidth: 3; fillColor: "transparent"
            strokeStyle: ShapePath.DashLine; dashPattern: [2, 3]
            PathSvg { path: s.touren.join(" ") }
        }
    }
    // Lieferroller: Paket mit Leuchtspur
    Repeater {
        model: s.touren.length
        Item {
            id: roller
            required property int index
            width: 1; height: 1
            Licht { anchors.centerIn: parent; width: 46; height: 46; farbe: roller.index % 3 ? s.c("akzent2") : s.c("akzent"); staerke: 0.7; kern: 0.1 }
            Rectangle { anchors.centerIn: parent; width: 12; height: 12; radius: 3; color: roller.index % 3 ? s.c("akzent2") : s.c("akzent") }
            PathAnimation {
                target: roller; running: true; paused: !s.laeuft; loops: Animation.Infinite
                duration: (9000 + s.zufall(roller.index + 3) * 7000) / s.tempo
                easing.type: Easing.InOutSine
                path: Path { PathSvg { path: s.touren.length > roller.index ? s.touren[roller.index] : "M 0 0" } }
            }
        }
    }
}
