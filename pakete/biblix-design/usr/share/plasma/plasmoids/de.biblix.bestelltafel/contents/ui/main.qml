/* Bibi Mac Bestelltafel: die Uhrzeit als Abholnummer. Jede Minute "ist eine Bestellung fertig". */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore

PlasmoidItem {
    id: wurzel
    readonly property color rot: "#e63131"
    readonly property color gelb: "#ffc72c"
    readonly property color creme: "#fff4dc"
    readonly property color tafel: "#24110e"

    property date jetzt: new Date()
    Timer { interval: 1000; running: true; repeat: true; onTriggered: wurzel.jetzt = new Date() }

    readonly property string nummer: Qt.formatTime(jetzt, "HH:mm")
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation
    toolTipMainText: "Bibi Mac · Nr. " + nummer
    toolTipSubText: jetzt.toLocaleDateString(Qt.locale("de_AT"), "dddd, d. MMMM yyyy")

    fullRepresentation: Item {
        Layout.preferredWidth: 260
        Layout.preferredHeight: 190
        Layout.minimumWidth: 200
        Layout.minimumHeight: 150

        Rectangle {
            id: brett
            anchors.fill: parent
            radius: 14
            color: wurzel.tafel
            border.color: wurzel.gelb
            border.width: 2
            clip: true

            Rectangle { width: parent.width; height: 34; color: wurzel.rot }
            Rectangle { y: 34; width: parent.width; height: 4; color: wurzel.gelb }
            Text {
                x: 14; y: 8
                text: "JETZT ABHOLBEREIT"
                color: wurzel.creme
                font.bold: true; font.pixelSize: 13; font.letterSpacing: 2
            }
            Rectangle {   // Lampe: blinkt, wenn eine neue Nummer kommt
                id: lampe
                anchors.right: parent.right; anchors.rightMargin: 14; y: 11
                width: 12; height: 12; radius: 6
                color: wurzel.gelb
                SequentialAnimation { id: blinken; loops: 4
                    NumberAnimation { target: lampe; property: "opacity"; to: 0.15; duration: 200 }
                    NumberAnimation { target: lampe; property: "opacity"; to: 1; duration: 200 } }
            }

            Text {
                id: nr
                anchors.horizontalCenter: parent.horizontalCenter
                y: 50
                text: "Nr. " + wurzel.nummer
                color: wurzel.gelb
                font.family: "DejaVu Sans Mono"; font.bold: true
                font.pixelSize: Math.min(parent.width / 6.2, 46)
                onTextChanged: { blinken.restart(); kippen.restart(); }
                transform: Scale { id: kipp; origin.y: nr.height / 2; yScale: 1 }
                SequentialAnimation { id: kippen
                    NumberAnimation { target: kipp; property: "yScale"; to: 0; duration: 140 }
                    NumberAnimation { target: kipp; property: "yScale"; to: 1; duration: 180; easing.type: Easing.OutBack } }
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: nr.bottom; anchors.topMargin: 4
                text: wurzel.jetzt.toLocaleDateString(Qt.locale("de_AT"), "dddd, d. MMMM")
                color: wurzel.creme
                font.pixelSize: 14
            }
            // Theke unten
            Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 22; color: wurzel.rot }
            Rectangle { anchors.bottom: parent.bottom; anchors.bottomMargin: 22; width: parent.width; height: 3; color: wurzel.gelb }
            Text {
                anchors.bottom: parent.bottom; anchors.bottomMargin: 4
                anchors.horizontalCenter: parent.horizontalCenter
                text: "AUF BIBLIX GEHT DAS."
                color: wurzel.creme; opacity: 0.85
                font.family: "DejaVu Sans Mono"; font.pixelSize: 11
            }
        }
    }
}
