/* Biblix Leistung: CPU- und GPU-Temperatur und -Auslastung als kleine Anzeige in der Taskleiste. */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PC3
import org.kde.ksysguard.sensors as Sensors
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: wurzel
    preferredRepresentation: compactRepresentation

    Sensors.Sensor { id: cpuLast; sensorId: "cpu/all/usage"; updateRateLimit: 2000 }
    Sensors.Sensor { id: cpuTemp; sensorId: "cpu/all/averageTemperature"; updateRateLimit: 2000 }
    Sensors.Sensor { id: gpu0Last; sensorId: "gpu/gpu0/usage"; updateRateLimit: 2000 }
    Sensors.Sensor { id: gpu1Last; sensorId: "gpu/gpu1/usage"; updateRateLimit: 2000 }
    Sensors.Sensor { id: gpu0Temp; sensorId: "gpu/gpu0/temperature"; updateRateLimit: 2000 }
    Sensors.Sensor { id: gpu1Temp; sensorId: "gpu/gpu1/temperature"; updateRateLimit: 2000 }

    readonly property real gpuLast: Math.max(gpu0Last.value || 0, gpu1Last.value || 0)
    readonly property real gpuTemp: Math.max(gpu0Temp.value || 0, gpu1Temp.value || 0)

    toolTipMainText: "Leistung"
    toolTipSubText: "CPU: " + Math.round(cpuLast.value || 0) + " % · " + Math.round(cpuTemp.value || 0) + " °C\n"
                  + "GPU: " + Math.round(gpuLast) + " % · " + Math.round(gpuTemp) + " °C"

    function farbe(t) {
        return t >= 85 ? Kirigami.Theme.negativeTextColor : (t >= 70 ? Kirigami.Theme.neutralTextColor : Kirigami.Theme.textColor);
    }

    compactRepresentation: RowLayout {
        spacing: Kirigami.Units.smallSpacing
        Layout.preferredWidth: implicitWidth
        Repeater {
            model: [
                { name: "CPU", last: cpuLast.value || 0, temp: cpuTemp.value || 0 },
                { name: "GPU", last: wurzel.gpuLast, temp: wurzel.gpuTemp }
            ]
            delegate: ColumnLayout {
                required property var modelData
                spacing: 0
                PC3.Label {
                    text: modelData.name + " " + Math.round(modelData.temp) + "°"
                    color: wurzel.farbe(modelData.temp)
                    font.family: "DejaVu Sans Mono"
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                }
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 3
                    radius: 1.5
                    color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.15)
                    Rectangle {
                        width: parent.width * Math.min(1, modelData.last / 100)
                        height: parent.height
                        radius: 1.5
                        color: Kirigami.Theme.highlightColor
                        Behavior on width { NumberAnimation { duration: 400 } }
                    }
                }
            }
        }
    }
}
