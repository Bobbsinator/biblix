/* Bibiplexx Leinwand: zeigt, was gerade laeuft (Musik oder Video, ueber MPRIS/playerctl).
   Laeuft nichts: "Saal frei", Klick oeffnet Bibiplexx. */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support

PlasmoidItem {
    id: wurzel
    readonly property color schwarz: "#07070c"
    readonly property color lila: "#7b2cbf"
    readonly property color pink: "#ff4d9d"
    readonly property color orange: "#ff8a00"
    readonly property color text: "#f2e9ff"
    readonly property color leise: "#a898c8"

    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation

    property string zustand: ""      // Playing | Paused | ""
    property string kuenstler: ""
    property string titel: ""
    readonly property bool laeuft: zustand === "Playing"

    readonly property string abfrage: "playerctl metadata --format '{{status}}|{{artist}}|{{title}}'"
    P5Support.DataSource {
        id: quelle
        engine: "executable"
        connectedSources: [wurzel.abfrage]
        interval: 2000
        onNewData: (q, daten) => {
            if (q !== wurzel.abfrage) { disconnectSource(q); return; }
            const t = (daten["stdout"] || "").trim().split("|");
            wurzel.zustand = t.length >= 3 ? t[0] : "";
            wurzel.kuenstler = t.length >= 3 ? t[1] : "";
            wurzel.titel = t.length >= 3 ? t.slice(2).join("|") : "";
        }
    }

    toolTipMainText: "Bibiplexx"
    toolTipSubText: zustand ? ((laeuft ? "Läuft: " : "Pause: ") + titel) : "Saal frei. Klicken öffnet Bibiplexx."

    fullRepresentation: MouseArea {
        Layout.preferredWidth: 300
        Layout.preferredHeight: 190
        Layout.minimumWidth: 230
        Layout.minimumHeight: 150
        cursorShape: Qt.PointingHandCursor
        onClicked: {
            if (wurzel.zustand) quelle.connectSource("playerctl play-pause");
            else quelle.connectSource("bibiplexx");
        }

        Rectangle { anchors.fill: parent; radius: 14; color: wurzel.schwarz }
        // Leinwand-Rahmen wie im Logo: lila Linien, pinke Eckstriche
        Item {
            id: rahmen
            x: 20; y: 18
            width: parent.width - 40; height: parent.height - 70
            Rectangle { width: parent.width; height: 2; color: wurzel.lila }
            Rectangle { y: parent.height; width: parent.width; height: 2; color: wurzel.lila }
            Repeater {
                model: [[0, 0, -1, -1], [1, 0, 1, -1], [0, 1, -1, 1], [1, 1, 1, 1]]
                Rectangle {
                    required property var modelData
                    width: 12; height: 2; color: wurzel.pink
                    x: modelData[0] * rahmen.width - 6 + modelData[2] * 3
                    y: modelData[1] * rahmen.height + modelData[3] * 3
                    rotation: modelData[2] * modelData[3] > 0 ? 45 : -45
                }
            }
            Column {
                anchors.centerIn: parent
                width: parent.width - 20
                spacing: 4
                Text {
                    width: parent.width
                    horizontalAlignment: Text.AlignHCenter
                    text: wurzel.zustand ? (wurzel.laeuft ? "JETZT IM SAAL" : "PAUSE") : "SAAL FREI"
                    color: wurzel.orange; font.bold: true; font.pixelSize: 11; font.letterSpacing: 2
                }
                Text {
                    width: parent.width
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    text: wurzel.zustand ? (wurzel.titel || "Unbekannter Titel") : "BIBIPLEXX"
                    color: wurzel.zustand ? wurzel.text : wurzel.pink
                    font.bold: true; font.pixelSize: wurzel.zustand ? 17 : 24
                }
                Text {
                    width: parent.width
                    horizontalAlignment: Text.AlignHCenter
                    elide: Text.ElideRight
                    visible: text !== ""
                    text: wurzel.zustand ? wurzel.kuenstler : "Klicken öffnet den Saal"
                    color: wurzel.leise; font.pixelSize: 12
                }
            }
        }
        // Sitzreihe: der mittlere Platz leuchtet orange, beim Abspielen leuchtet die Reihe nacheinander auf
        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom; anchors.bottomMargin: 14
            spacing: 6
            Repeater {
                model: 7
                Rectangle {
                    required property int index
                    width: 22; height: 18; radius: 5
                    border.color: wurzel.lila; border.width: 1
                    color: index === 3 ? wurzel.orange : "#1a1030"
                    SequentialAnimation on opacity {
                        running: wurzel.laeuft && index !== 3
                        loops: Animation.Infinite
                        PauseAnimation { duration: index * 120 }
                        NumberAnimation { to: 0.45; duration: 500 }
                        NumberAnimation { to: 1; duration: 500 }
                        PauseAnimation { duration: (6 - index) * 120 }
                    }
                }
            }
        }
    }
}
