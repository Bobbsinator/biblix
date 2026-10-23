/* Nassmacher Pegel: belegter Arbeitsspeicher als Wasserstand, mit Wellen. */
import QtQuick
import QtQuick.Layouts
import QtQuick.Shapes
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.ksysguard.sensors as Sensors

PlasmoidItem {
    id: wurzel
    readonly property color grund: "#03242a"
    readonly property color cyan: "#22d3e6"
    readonly property color orange: "#ffb020"
    readonly property color text: "#e6fbfd"
    readonly property color leise: "#8ac6cf"

    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation

    Sensors.Sensor { id: belegt; sensorId: "memory/physical/used"; updateRateLimit: 2000 }
    Sensors.Sensor { id: gesamt; sensorId: "memory/physical/total"; updateRateLimit: 10000 }
    readonly property real anteil: gesamt.value > 0 ? Math.max(0, Math.min(1, belegt.value / gesamt.value)) : 0
    function gb(b) { return (b / 1024 / 1024 / 1024).toFixed(1).replace(".", ","); }
    // Sensoren liefern Bytes oder KiB je nach Version: an der Gesamtgroesse erkennen
    function groesse(b) { return gesamt.value > 1e9 ? gb(b) : (b / 1024 / 1024).toFixed(1).replace(".", ","); }

    toolTipMainText: "Nassmacher Pegel " + Math.round(anteil * 100) + " %"
    toolTipSubText: groesse(belegt.value || 0) + " von " + groesse(gesamt.value || 0) + " GB Arbeitsspeicher belegt"

    fullRepresentation: Item {
        Layout.preferredWidth: 180
        Layout.preferredHeight: 230
        Layout.minimumWidth: 140
        Layout.minimumHeight: 180

        Rectangle {
            anchors.fill: parent
            radius: 18
            color: wurzel.grund
            border.color: wurzel.cyan
            border.width: 2
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter; y: 12
            text: "PEGEL"; color: wurzel.cyan; font.bold: true; font.pixelSize: 13; font.letterSpacing: 3
        }
        // Becken
        Item {
            id: becken
            x: 20; y: 38
            width: parent.width - 40
            height: parent.height - 92
            clip: true
            Rectangle { anchors.fill: parent; radius: 10; color: "#0a434d"; border.color: "#146070" }
            Item {
                id: wasser
                width: parent.width
                height: parent.height * wurzel.anteil
                y: parent.height - height
                Behavior on height { NumberAnimation { duration: 900; easing.type: Easing.InOutQuad } }
                property real phase: 0
                NumberAnimation on phase { from: 0; to: Math.PI * 2; duration: 2600; loops: Animation.Infinite }
                Shape {
                    anchors.fill: parent
                    ShapePath {
                        fillColor: Qt.rgba(0.133, 0.827, 0.902, 0.75)
                        strokeColor: "transparent"
                        startX: 0; startY: 6 + Math.sin(wasser.phase) * 4
                        PathCubic {
                            x: wasser.width; y: 6 + Math.sin(wasser.phase + Math.PI) * 4
                            control1X: wasser.width * 0.35; control1Y: 6 + Math.sin(wasser.phase + 1.3) * 9
                            control2X: wasser.width * 0.65; control2Y: 6 + Math.sin(wasser.phase + 2.6) * 9
                        }
                        PathLine { x: wasser.width; y: wasser.height }
                        PathLine { x: 0; y: wasser.height }
                    }
                }
            }
            // Markierungen am Rand
            Repeater {
                model: 4
                Rectangle {
                    required property int index
                    x: 0; y: becken.height * (index + 1) / 5
                    width: 10; height: 2; color: wurzel.leise; opacity: 0.6
                }
            }
            // Warnmarke bei 90 %
            Rectangle { y: becken.height * 0.1; width: becken.width; height: 1; color: wurzel.orange; opacity: 0.7 }
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom; anchors.bottomMargin: 30
            text: Math.round(wurzel.anteil * 100) + " %"
            color: wurzel.anteil > 0.9 ? wurzel.orange : wurzel.text
            font.bold: true; font.pixelSize: 20
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom; anchors.bottomMargin: 12
            text: wurzel.groesse(belegt.value || 0) + " / " + wurzel.groesse(gesamt.value || 0) + " GB"
            color: wurzel.leise; font.family: "DejaVu Sans Mono"; font.pixelSize: 11
        }
    }
}
