/* Bibi Tech Stockwerk: CPU-Last als Stockwerk (EG bis 10). Der Aufzug faehrt mit, die Fenster leuchten. */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.ksysguard.sensors as Sensors

PlasmoidItem {
    id: wurzel
    readonly property color grund: "#0f141c"
    readonly property color karte: "#1a2029"
    readonly property color rand: "#313a48"
    readonly property color blau: "#378add"
    readonly property color gelb: "#ffd400"
    readonly property color text: "#e8ecf2"

    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation

    Sensors.Sensor { id: cpuLast; sensorId: "cpu/all/usage"; updateRateLimit: 1500 }
    Sensors.Sensor { id: cpuTemp; sensorId: "cpu/all/averageTemperature"; updateRateLimit: 3000 }

    readonly property real last: Math.max(0, Math.min(100, cpuLast.value || 0))
    readonly property int etage: Math.round(last / 10)
    property int vorher: 0
    property bool hoch: true
    onEtageChanged: { hoch = etage >= vorher; vorher = etage; }

    toolTipMainText: "Bibi Tech · Stockwerk " + (etage === 0 ? "EG" : etage)
    toolTipSubText: "CPU " + Math.round(last) + " % · " + Math.round(cpuTemp.value || 0) + " °C"

    fullRepresentation: Item {
        Layout.preferredWidth: 230
        Layout.preferredHeight: 230
        Layout.minimumWidth: 170
        Layout.minimumHeight: 170

        Rectangle {
            anchors.fill: parent
            radius: 6
            color: wurzel.grund
            border.color: wurzel.rand
            border.width: 1
            // Bauplan-Raster
            Repeater {
                model: Math.floor(parent.width / 24)
                Rectangle { x: index * 24; width: 1; height: parent.height; color: wurzel.blau; opacity: 0.08 }
            }
            Repeater {
                model: Math.floor(parent.height / 24)
                Rectangle { y: index * 24; height: 1; width: parent.width; color: wurzel.blau; opacity: 0.08 }
            }
        }

        // Leuchtanzeige links
        Column {
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.margins: 14
            spacing: 4
            Text { text: "STOCKWERK"; color: wurzel.blau; font.family: "DejaVu Sans Mono"; font.pixelSize: 10; font.bold: true; font.letterSpacing: 2 }
            Rectangle {
                width: 92; height: 58; radius: 6
                color: "#05070a"
                border.color: wurzel.rand
                Text {
                    anchors.left: parent.left; anchors.leftMargin: 8
                    anchors.verticalCenter: parent.verticalCenter
                    text: wurzel.hoch ? "▲" : "▼"
                    color: wurzel.gelb; font.pixelSize: 16
                    opacity: blink.running ? 1 : 0.35
                    SequentialAnimation on opacity { id: blink; running: false; loops: 3
                        NumberAnimation { to: 0.2; duration: 180 } NumberAnimation { to: 1; duration: 180 } }
                }
                Text {
                    anchors.right: parent.right; anchors.rightMargin: 10
                    anchors.verticalCenter: parent.verticalCenter
                    text: wurzel.etage === 0 ? "EG" : wurzel.etage
                    color: wurzel.gelb
                    font.family: "DejaVu Sans Mono"; font.bold: true; font.pixelSize: 32
                    onTextChanged: blink.restart()
                }
            }
            Item { width: 1; height: 6 }
            Text { text: "CPU " + Math.round(wurzel.last) + " %"; color: wurzel.text; font.family: "DejaVu Sans Mono"; font.pixelSize: 13 }
            Text {
                text: Math.round(cpuTemp.value || 0) + " °C"
                color: (cpuTemp.value || 0) >= 85 ? "#e24b4a" : ((cpuTemp.value || 0) >= 70 ? wurzel.gelb : wurzel.text)
                font.family: "DejaVu Sans Mono"; font.pixelSize: 13
            }
        }

        // Tower rechts mit 10 Stockwerken + EG und Panorama-Aufzug
        Item {
            id: turm
            anchors.right: parent.right
            anchors.rightMargin: 22
            anchors.top: parent.top
            anchors.topMargin: 22
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 18
            width: 62
            readonly property real stock: height / 11

            Rectangle {
                anchors.fill: parent
                color: Qt.rgba(0.216, 0.541, 0.867, 0.18)
                border.color: wurzel.blau
                border.width: 1.5
                radius: 2
            }
            Repeater {
                model: 11
                Row {
                    id: reihe
                    required property int index
                    readonly property bool an: index <= wurzel.etage
                    x: 7
                    y: turm.height - (index + 1) * turm.stock + 3
                    spacing: 5
                    Repeater {
                        model: 4
                        Rectangle {
                            width: 8; height: Math.max(3, turm.stock - 6)
                            color: reihe.an ? wurzel.gelb : "#ffffff"
                            opacity: reihe.an ? 0.9 : 0.12
                            Behavior on opacity { NumberAnimation { duration: 300 } }
                        }
                    }
                }
            }
            // Aufzugsschacht und Kabine
            Rectangle { x: turm.width + 6; width: 1; height: turm.height; color: wurzel.blau; opacity: 0.6 }
            Rectangle { x: turm.width + 15; width: 1; height: turm.height; color: wurzel.blau; opacity: 0.6 }
            Rectangle {
                x: turm.width + 7
                width: 8; height: Math.max(8, turm.stock - 2); radius: 2
                color: wurzel.gelb
                y: turm.height - (wurzel.etage + 1) * turm.stock + 1
                Behavior on y { NumberAnimation { duration: 700; easing.type: Easing.InOutCubic } }
            }
            // Antenne mit Blinklicht
            Rectangle { anchors.horizontalCenter: parent.horizontalCenter; y: -14; width: 2; height: 14; color: wurzel.blau }
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter; y: -18; width: 6; height: 6; radius: 3
                color: "#ff4a4a"
                SequentialAnimation on opacity { loops: Animation.Infinite
                    NumberAnimation { to: 0.15; duration: 700 } NumberAnimation { to: 1; duration: 700 } }
            }
        }
    }
}
