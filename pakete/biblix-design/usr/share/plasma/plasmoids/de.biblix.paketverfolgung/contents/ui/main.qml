/* Bibi Delivery Paketverfolgung: Downloads als Lieferung unterwegs, wartende Updates als Pakete zur Zustellung.
   Klick oeffnet die Updates im S-Launcher. */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.ksysguard.sensors as Sensors

PlasmoidItem {
    id: wurzel
    readonly property color grund: "#05102b"
    readonly property color karte: "#10255a"
    readonly property color gelb: "#ffd000"
    readonly property color blau: "#1e6bff"
    readonly property color text: "#ffffff"
    readonly property color leise: "#9fb0d8"

    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation

    Sensors.Sensor { id: runter; sensorId: "network/all/download"; updateRateLimit: 1500 }
    readonly property real rate: runter.value || 0          // Byte pro Sekunde
    readonly property bool unterwegs: rate > 150 * 1024
    property int updates: 0
    readonly property int station: unterwegs ? 2 : (updates > 0 ? 1 : 3)   // 1 bestellt (Updates warten), 2 unterwegs, 3 zugestellt

    readonly property string pruefen: "sh -c 'apt list --upgradable 2>/dev/null | grep -c upgradable'"
    P5Support.DataSource {
        id: quelle
        engine: "executable"
        connectedSources: [wurzel.pruefen]
        interval: 10 * 60 * 1000
        onNewData: (q, daten) => {
            if (q === wurzel.pruefen) wurzel.updates = parseInt((daten["stdout"] || "0").trim()) || 0;
            else disconnectSource(q);
        }
    }

    function menge(b) {
        if (b >= 1024 * 1024) return (b / 1024 / 1024).toFixed(1).replace(".", ",") + " MB/s";
        return Math.round(b / 1024) + " KB/s";
    }
    readonly property string status: unterwegs ? "Unterwegs: " + menge(rate)
                                   : (updates > 0 ? updates + " Update" + (updates > 1 ? "s" : "") + " zur Zustellung bereit"
                                                  : "Alles zugestellt")
    toolTipMainText: "Bibi Delivery"
    toolTipSubText: status + (updates > 0 ? "\nKlicken: Updates öffnen" : "")

    fullRepresentation: MouseArea {
        Layout.preferredWidth: 280
        Layout.preferredHeight: 160
        Layout.minimumWidth: 220
        Layout.minimumHeight: 130
        cursorShape: Qt.PointingHandCursor
        onClicked: quelle.connectSource("s-launcher --updates")

        Rectangle {
            anchors.fill: parent
            radius: 12
            color: wurzel.grund
            border.color: wurzel.blau
            border.width: 2
        }
        Text {
            x: 14; y: 10
            text: "PAKETVERFOLGUNG"
            color: wurzel.gelb; font.bold: true; font.pixelSize: 12; font.letterSpacing: 2
        }
        // Strecke mit drei Stationen
        Item {
            id: strecke
            x: 24; y: 52
            width: parent.width - 48; height: 30
            Rectangle { y: 13; width: parent.width; height: 4; radius: 2; color: wurzel.karte }
            Rectangle {
                y: 13; height: 4; radius: 2; color: wurzel.gelb
                width: parent.width * (wurzel.station - 1) / 2
                Behavior on width { NumberAnimation { duration: 600; easing.type: Easing.InOutCubic } }
            }
            Repeater {
                model: ["Bestellt", "Unterwegs", "Zugestellt"]
                Item {
                    required property int index
                    required property string modelData
                    x: strecke.width * index / 2 - 7
                    Rectangle {
                        y: 8; width: 14; height: 14; radius: 7
                        color: index + 1 <= wurzel.station ? wurzel.gelb : wurzel.karte
                        border.color: wurzel.gelb; border.width: 2
                    }
                    Text {
                        y: 28; x: 7 - width / 2
                        text: modelData
                        color: index + 1 === wurzel.station ? wurzel.text : wurzel.leise
                        font.pixelSize: 10
                    }
                }
            }
            // Paket, das faehrt (wackelt, solange etwas unterwegs ist)
            Rectangle {
                width: 16; height: 13; radius: 2
                color: "#c58a3a"; border.color: "#7a4f1c"
                x: strecke.width * (wurzel.station - 1) / 2 - 8
                y: -6
                Behavior on x { NumberAnimation { duration: 700; easing.type: Easing.InOutCubic } }
                Rectangle { anchors.centerIn: parent; width: 2; height: parent.height; color: "#7a4f1c" }
                SequentialAnimation on rotation {
                    running: wurzel.unterwegs; loops: Animation.Infinite
                    NumberAnimation { to: 6; duration: 160 } NumberAnimation { to: -6; duration: 160 }
                }
            }
        }
        Text {
            anchors.left: parent.left; anchors.leftMargin: 14
            anchors.bottom: parent.bottom; anchors.bottomMargin: 12
            text: wurzel.status
            color: wurzel.text
            font.pixelSize: 13; font.bold: true
        }
    }
}
