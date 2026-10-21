/* Biblix Updates: zeigt, wenn Biblix-Pakete aktualisiert werden können. Klick öffnet den S-Launcher (Updates). */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: wurzel
    property int anzahl: 0
    readonly property string pruefen: "sh -c 'apt list --upgradable 2>/dev/null | grep -c \"^biblix\"'"
    preferredRepresentation: compactRepresentation
    toolTipMainText: "Biblix-Updates"
    toolTipSubText: anzahl > 0 ? (anzahl + " Biblix-Update" + (anzahl > 1 ? "s" : "") + " bereit. Klicken zum Installieren.")
                               : "DU BIST AUF DEM AKTUELLEN STAND."

    P5Support.DataSource {
        id: quelle
        engine: "executable"
        connectedSources: [wurzel.pruefen]
        interval: 15 * 60 * 1000
        onNewData: (q, daten) => {
            if (q === wurzel.pruefen) {
                wurzel.anzahl = parseInt((daten["stdout"] || "0").trim()) || 0;
            } else {
                disconnectSource(q);
            }
        }
    }

    compactRepresentation: MouseArea {
        Layout.preferredWidth: height
        hoverEnabled: true
        onClicked: quelle.connectSource("s-launcher --updates")
        Kirigami.Icon {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            source: wurzel.anzahl > 0 ? "update-high" : "update-none"
            opacity: wurzel.anzahl > 0 ? 1 : 0.4
        }
        Rectangle {
            visible: wurzel.anzahl > 0
            anchors.right: parent.right
            anchors.top: parent.top
            width: Kirigami.Units.gridUnit * 0.9
            height: width
            radius: width / 2
            color: Kirigami.Theme.highlightColor
            Text {
                anchors.centerIn: parent
                text: wurzel.anzahl
                color: Kirigami.Theme.highlightedTextColor
                font.pixelSize: parent.height * 0.65
                font.bold: true
            }
        }
    }
}
