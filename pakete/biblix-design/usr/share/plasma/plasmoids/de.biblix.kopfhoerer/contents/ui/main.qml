/* Biblix Tonausgabe: ein Klick wechselt zur nächsten Ausgabe (z. B. JBL-Headset <-> Lautsprecher). */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: wurzel
    property string ausgabe: ""
    readonly property bool kopfhoerer: /headset|headphone|kopfh|jbl|quantum|usb/i.test(ausgabe)
    readonly property string abfrage: "/usr/lib/biblix/biblix-tonausgabe"
    preferredRepresentation: compactRepresentation
    toolTipMainText: "Tonausgabe"
    toolTipSubText: (ausgabe || "unbekannt") + "\nKlicken zum Wechseln"

    P5Support.DataSource {
        id: quelle
        engine: "executable"
        connectedSources: [wurzel.abfrage]
        interval: 5000
        onNewData: (q, daten) => {
            wurzel.ausgabe = (daten["stdout"] || "").trim();
            if (q !== wurzel.abfrage) {
                disconnectSource(q);
            }
        }
    }

    compactRepresentation: MouseArea {
        Layout.preferredWidth: height
        hoverEnabled: true
        onClicked: quelle.connectSource(wurzel.abfrage + " wechseln")
        Kirigami.Icon {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            source: wurzel.kopfhoerer ? "audio-headphones-symbolic" : "audio-speakers-symbolic"
            isMask: true
            color: wurzel.kopfhoerer ? Kirigami.Theme.highlightColor : Kirigami.Theme.textColor
        }
    }
}
