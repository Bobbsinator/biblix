// Prompt: ein Biblix-Terminal tippt Bibi-Sprüche
import QtQuick

Szene {
    id: s

    readonly property var liste: {
        const l = s.sprueche.filter(z => !z.trim().startsWith("#"));
        return l.length ? l : ["AUF BIBLIX GEHT DAS.", "DEIN SYSTEM. DEIN PROBLEM."];
    }
    readonly property real schrift: Math.max(18, s.height / 30)
    property string aktuell: ""
    property string ziel: ""
    property int nr: 0

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.c("grund") }
            GradientStop { position: 1.0; color: s.mix("grund", "flaeche", 0.6) }
        }
    }
    // Grosses Prompt-B im Hintergrund
    Text {
        anchors.right: parent.right; anchors.bottom: parent.bottom
        anchors.margins: s.height * 0.05
        text: ">B"
        font.family: "DejaVu Sans Mono"; font.bold: true
        font.pixelSize: s.height * 0.42
        color: s.c("akzent", 0.07)
    }
    ListModel { id: zeilen }
    Column {
        x: s.width * 0.14; y: s.height * 0.3
        width: s.width * 0.62
        spacing: s.schrift * 0.55
        Repeater {
            model: zeilen
            Text {
                required property string zeile
                required property int index
                width: parent.width
                wrapMode: Text.Wrap
                textFormat: Text.PlainText
                font.family: "DejaVu Sans Mono"; font.pixelSize: s.schrift
                color: s.c("text", 0.35 + 0.65 * (index + 1) / Math.max(1, zeilen.count))
                text: "> " + zeile
            }
        }
        Row {
            spacing: 0
            Text {
                font.family: "DejaVu Sans Mono"; font.pixelSize: s.schrift; font.bold: true
                color: s.c("akzent"); text: "bibi@biblix:~$ "
            }
            Text {
                font.family: "DejaVu Sans Mono"; font.pixelSize: s.schrift
                color: s.c("text"); text: s.aktuell
            }
            Rectangle {
                width: s.schrift * 0.6; height: s.schrift * 1.15
                color: s.c("akzent2")
                SequentialAnimation on opacity {
                    loops: Animation.Infinite; paused: !s.laeuft
                    NumberAnimation { to: 0; duration: 0 }
                    PauseAnimation { duration: 530 }
                    NumberAnimation { to: 1; duration: 0 }
                    PauseAnimation { duration: 530 }
                }
            }
        }
    }
    function naechster() {
        s.nr = Math.floor(Math.random() * s.liste.length);
        s.ziel = s.liste[s.nr];
        s.aktuell = "";
    }
    Timer {
        id: tippen
        interval: 55 / s.tempo; repeat: true; running: s.laeuft
        property int warten: 0
        onTriggered: {
            if (warten > 0) { warten--; return; }
            if (s.ziel === "") { s.naechster(); return; }
            if (s.aktuell.length < s.ziel.length) {
                s.aktuell = s.ziel.slice(0, s.aktuell.length + 1);
                interval = (35 + Math.random() * 70) / s.tempo;
                return;
            }
            // Spruch fertig: als Zeile ablegen, kurz warten, naechster
            zeilen.append({ zeile: s.ziel });
            while (zeilen.count > 5) zeilen.remove(0);
            s.ziel = "";
            s.aktuell = "";
            warten = 40;
        }
    }
}
