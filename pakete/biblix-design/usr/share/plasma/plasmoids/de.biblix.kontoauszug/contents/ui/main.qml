/* Bibi Budget Bank Kontoauszug: freier Speicherplatz jeder Platte als Guthaben. */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support

PlasmoidItem {
    id: wurzel
    readonly property color grund: "#0b1f15"
    readonly property color karte: "#1c432f"
    readonly property color gold: "#c9a227"
    readonly property color text: "#efe6cf"
    readonly property color leise: "#a8b59c"
    readonly property color rot: "#d0553f"

    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation

    property var konten: []
    readonly property string abfrage: "df -B1 --output=target,size,avail -x tmpfs -x devtmpfs -x efivarfs -x squashfs -x overlay -x vfat"
    P5Support.DataSource {
        id: quelle
        engine: "executable"
        connectedSources: [wurzel.abfrage]
        interval: 60 * 1000
        onNewData: (q, daten) => {
            const liste = [];
            const zeilen = (daten["stdout"] || "").split("\n").slice(1);
            for (const z of zeilen) {
                const t = z.trim().split(/\s+/);
                if (t.length < 3) continue;
                const ort = t[0];
                if (!(ort === "/" || ort.startsWith("/home") || ort.startsWith("/media") || ort.startsWith("/mnt") || ort.startsWith("/run/media")))
                    continue;
                const gross = Number(t[1]), frei = Number(t[2]);
                if (!gross) continue;
                const name = ort === "/" ? "Hauptkonto" : ort.split("/").pop();
                liste.push({ name: name, ort: ort, gross: gross, frei: frei });
            }
            wurzel.konten = liste.slice(0, 5);
        }
    }

    function gb(b) {
        const g = b / 1e9;
        return g >= 1000 ? (g / 1000).toFixed(2).replace(".", ",") + " TB" : Math.round(g) + " GB";
    }
    readonly property real gesamtFrei: konten.reduce((s, k) => s + k.frei, 0)
    toolTipMainText: "Bibi Budget Bank"
    toolTipSubText: "Guthaben gesamt: " + gb(gesamtFrei) + " frei"

    fullRepresentation: Item {
        Layout.preferredWidth: 280
        Layout.preferredHeight: 70 + Math.max(1, wurzel.konten.length) * 44
        Layout.minimumWidth: 220

        Rectangle {
            anchors.fill: parent
            radius: 4
            color: wurzel.grund
            border.color: wurzel.gold
            border.width: 1
        }
        Rectangle { x: 6; y: 6; width: parent.width - 12; height: parent.height - 12; radius: 2; color: "transparent"; border.color: wurzel.gold; opacity: 0.35 }
        Text {
            x: 16; y: 14
            text: "KONTOAUSZUG"
            color: wurzel.gold; font.family: "DejaVu Serif"; font.bold: true; font.pixelSize: 14; font.letterSpacing: 3
        }
        Text {
            anchors.right: parent.right; anchors.rightMargin: 16; y: 16
            text: Qt.formatDate(new Date(), "dd.MM.yyyy")
            color: wurzel.leise; font.family: "DejaVu Sans Mono"; font.pixelSize: 11
        }
        Rectangle { x: 16; y: 38; width: parent.width - 32; height: 1; color: wurzel.gold; opacity: 0.6 }

        Column {
            x: 16; y: 48
            width: parent.width - 32
            spacing: 8
            Repeater {
                model: wurzel.konten
                Column {
                    required property var modelData
                    width: parent.width
                    spacing: 3
                    readonly property real anteil: 1 - modelData.frei / modelData.gross
                    readonly property bool knapp: modelData.frei / modelData.gross < 0.1
                    Item {
                        width: parent.width; height: 16
                        Text { text: modelData.name; color: wurzel.text; font.pixelSize: 12; font.bold: true }
                        Text {
                            anchors.right: parent.right
                            text: (knapp ? "Dispo! " : "") + wurzel.gb(modelData.frei) + " frei"
                            color: knapp ? wurzel.rot : wurzel.gold
                            font.family: "DejaVu Sans Mono"; font.pixelSize: 12
                        }
                    }
                    Rectangle {
                        width: parent.width; height: 6; radius: 3; color: wurzel.karte
                        Rectangle {
                            width: parent.width * Math.min(1, anteil); height: parent.height; radius: 3
                            color: knapp ? wurzel.rot : wurzel.gold
                            Behavior on width { NumberAnimation { duration: 500 } }
                        }
                    }
                }
            }
        }
    }
}
