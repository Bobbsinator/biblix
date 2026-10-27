/*
    Biblix-Uhr: zeigt die Zeit im Stil der Welt aus Biblix Design.
    typenschild: Klartext · tower: Etagenanzeige · bank: Fallblatt · mac: Abholnummer ·
    delivery: Zustellzeit · plexx: Kinoschild mit Lichtern · nass: Badekappe. Klick: Kalender.
*/
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: uhr

    readonly property var standard: ({ karte: "#232a35", rand: "#313a48", text: "#e8ecf2", leise: "#8b95a5", akzent: "#378add", akzent2: "#ffd400" })
    readonly property var f: {
        let x = {};
        try { x = JSON.parse(Plasmoid.configuration.farben || "{}"); } catch (e) { x = {}; }
        return Object.assign({}, standard, x);
    }
    readonly property string welt: Plasmoid.configuration.welt || "typenschild"
    property date jetzt: new Date()
    readonly property string zeit: Qt.formatTime(jetzt, "hh:mm")
    readonly property var de: Qt.locale("de_DE")
    readonly property string datum: (de.toString(jetzt, "ddd").replace(".", "") + " " + de.toString(jetzt, "dd.MM.")).toUpperCase()

    Timer {
        interval: 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: uhr.jetzt = new Date()
    }

    toolTipMainText: de.toString(jetzt, "dddd, d. MMMM yyyy")
    toolTipSubText: Qt.formatTime(jetzt, "hh:mm:ss")
    preferredRepresentation: compactRepresentation

    compactRepresentation: MouseArea {
        id: anzeige
        readonly property real h: parent ? parent.height : 44
        Layout.minimumWidth: inhalt.item ? inhalt.item.implicitWidth : h * 2.5
        Layout.preferredWidth: Layout.minimumWidth
        onClicked: uhr.expanded = !uhr.expanded
        Loader {
            id: inhalt
            anchors.fill: parent
            sourceComponent: ({ tower: tower, bank: bank, mac: mac, plexx: plexx, nass: nass })[uhr.welt] || klartext
        }
        Component {
            id: klartext
            Item {
                implicitWidth: Math.max(z.implicitWidth, d.implicitWidth) + anzeige.h * 0.5
                Column {
                    anchors.centerIn: parent
                    spacing: -2
                    Text { id: z; anchors.horizontalCenter: parent.horizontalCenter; text: uhr.zeit; color: uhr.welt === "delivery" ? "#ffd400" : uhr.f.text
                           font.family: "DejaVu Sans Mono"; font.bold: true; font.pixelSize: anzeige.h * 0.38 }
                    Text { id: d; anchors.horizontalCenter: parent.horizontalCenter; text: uhr.datum; color: uhr.f.leise
                           font.family: "DejaVu Sans Mono"; font.pixelSize: anzeige.h * 0.2 }
                }
            }
        }
        Component {
            id: tower
            Item {
                implicitWidth: t.implicitWidth + anzeige.h * 0.7
                Rectangle {
                    anchors.fill: parent; anchors.margins: anzeige.h * 0.12
                    radius: 4; color: "#120c04"; border.color: "#2a2010"
                    Text { id: t; anchors.centerIn: parent; text: uhr.zeit; color: "#ffb020"
                           font.family: "DejaVu Sans Mono"; font.bold: true; font.pixelSize: anzeige.h * 0.48 }
                }
            }
        }
        Component {
            id: bank
            Item {
                implicitWidth: zeile.implicitWidth + anzeige.h * 0.4
                Row {
                    id: zeile
                    anchors.centerIn: parent
                    spacing: 2
                    Repeater {
                        model: uhr.zeit.split("")
                        Item {
                            required property string modelData
                            width: modelData === ":" ? anzeige.h * 0.18 : anzeige.h * 0.38
                            height: anzeige.h * 0.68
                            Rectangle { visible: modelData !== ":"; anchors.fill: parent; radius: 3; color: "#1d1d1d" }
                            Rectangle { visible: modelData !== ":"; width: parent.width; height: 1; y: parent.height / 2; color: "#050505" }
                            Text { anchors.centerIn: parent; text: modelData; color: "#f3e9cf"
                                   font.family: "DejaVu Sans Mono"; font.bold: true; font.pixelSize: anzeige.h * 0.44 }
                        }
                    }
                }
            }
        }
        Component {
            id: mac
            Item {
                implicitWidth: Math.max(m1.implicitWidth, m2.implicitWidth) + anzeige.h * 0.6
                Rectangle {
                    anchors.fill: parent; anchors.margins: anzeige.h * 0.1
                    radius: 5; color: "#0b0b0b"
                    Column {
                        anchors.centerIn: parent
                        spacing: -2
                        Text { id: m1; text: "ABHOLBEREIT"; color: "#b0b0b0"; font.family: "DejaVu Sans Mono"; font.bold: true; font.pixelSize: anzeige.h * 0.17 }
                        Text { id: m2; text: uhr.zeit; color: "#6fe36f"; font.family: "DejaVu Sans Mono"; font.bold: true; font.pixelSize: anzeige.h * 0.36 }
                    }
                }
            }
        }
        Component {
            id: plexx
            Item {
                implicitWidth: p.implicitWidth + anzeige.h * 0.8
                Rectangle {
                    id: schild
                    anchors.fill: parent; anchors.margins: anzeige.h * 0.1
                    radius: 4; color: "#1a1030"; border.color: "#ff8a3d"; border.width: 1
                    Text { id: p; anchors.centerIn: parent; text: uhr.zeit; color: "#ffe9c2"
                           font.family: "DejaVu Sans Mono"; font.bold: true; font.pixelSize: anzeige.h * 0.4 }
                    Repeater {
                        model: Math.floor(schild.width / 8)
                        Rectangle {
                            required property int index
                            x: 4 + index * 8; y: 1.5; width: 3; height: 3; radius: 1.5
                            color: (index + Math.floor(uhr.jetzt.getSeconds())) % 3 === 0 ? "#ffd27a" : "#5a3a20"
                        }
                    }
                }
            }
        }
        Component {
            id: nass
            Item {
                implicitWidth: n.implicitWidth + anzeige.h * 0.8
                Rectangle {
                    anchors.fill: parent; anchors.margins: anzeige.h * 0.12
                    radius: height / 2; color: "#22d3e6"
                    Text { id: n; anchors.centerIn: parent; text: uhr.zeit; color: "#06323a"
                           font.family: "DejaVu Sans Mono"; font.bold: true; font.pixelSize: anzeige.h * 0.4 }
                }
            }
        }
    }

    fullRepresentation: ColumnLayout {
        Layout.preferredWidth: Kirigami.Units.gridUnit * 18
        Layout.preferredHeight: Kirigami.Units.gridUnit * 17
        spacing: Kirigami.Units.smallSpacing
        property int monat: uhr.jetzt.getMonth()
        property int jahr: uhr.jetzt.getFullYear()
        RowLayout {
            Layout.fillWidth: true
            QQC2.ToolButton { icon.name: "go-previous"; onClicked: { if (parent.parent.monat === 0) { parent.parent.monat = 11; parent.parent.jahr--; } else parent.parent.monat--; } }
            Kirigami.Heading {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                level: 3
                text: uhr.de.standaloneMonthName(parent.parent.monat) + " " + parent.parent.jahr
            }
            QQC2.ToolButton { icon.name: "go-next"; onClicked: { if (parent.parent.monat === 11) { parent.parent.monat = 0; parent.parent.jahr++; } else parent.parent.monat++; } }
        }
        QQC2.DayOfWeekRow {
            Layout.fillWidth: true
            locale: uhr.de
        }
        QQC2.MonthGrid {
            id: gitter
            Layout.fillWidth: true
            Layout.fillHeight: true
            month: parent.monat
            year: parent.jahr
            locale: uhr.de
            delegate: Rectangle {
                required property var model
                readonly property bool heute: model.today
                radius: height / 2
                color: heute ? uhr.f.akzent : "transparent"
                opacity: model.month === gitter.month ? 1 : 0.4
                Text {
                    anchors.centerIn: parent
                    text: parent.model.day
                    color: parent.heute ? "#ffffff" : Kirigami.Theme.textColor
                    font.bold: parent.heute
                }
            }
        }
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: uhr.de.toString(uhr.jetzt, "dddd, d. MMMM yyyy")
            color: Kirigami.Theme.disabledTextColor
        }
    }
}
