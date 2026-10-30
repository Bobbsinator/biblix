/*
    Biblix: Diashow waehrend der Installation (Calamares, slideshowAPI 2).
    Nur QtQuick, keine Bilder noetig: Karten im Bibi-Tech-Look (Graphit, Electric Blue, gelber B-Akzent).
    Grundlage: show.qml aus calamares-settings-debian (GPL-3.0-or-later).
*/
import QtQuick 2.0;
import calamares.slideshow 1.0;

Presentation
{
    id: presentation

    readonly property color grund: "#0f141c"
    readonly property color karte: "#232a35"
    readonly property color rand: "#313a48"
    readonly property color text: "#e8ecf2"
    readonly property color leise: "#8b95a5"
    readonly property color akzent: "#378add"
    readonly property color gelb: "#ffd400"

    Timer {
        interval: 12000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    // Eine Folie: Ueberschrift, Text, kleines Zeichen links
    component Folie: Slide {
        id: folie
        property string titel
        property string inhalt
        property string zeichen: "B"
        Rectangle {
            anchors.fill: parent
            color: presentation.grund
        }
        Rectangle {
            id: kachel
            anchors.centerIn: parent
            width: Math.min(parent.width - 60, 640)
            height: spalte.height + 64
            radius: 22
            color: presentation.karte
            border.color: presentation.rand
            border.width: 1
            Rectangle {   // Akzentstreifen oben
                anchors { left: parent.left; right: parent.right; top: parent.top; leftMargin: 22; rightMargin: 22; topMargin: 1 }
                height: 4
                radius: 2
                color: presentation.akzent
            }
            Row {
                id: spalte
                anchors { left: parent.left; right: parent.right; top: parent.top; margins: 32 }
                spacing: 24
                Rectangle {
                    width: 72; height: 72; radius: 18
                    color: presentation.akzent
                    Text {
                        anchors.centerIn: parent
                        text: folie.zeichen
                        color: "#ffffff"
                        font { family: "DejaVu Sans"; bold: true; pixelSize: 38 }
                    }
                }
                Column {
                    width: kachel.width - 64 - 96
                    spacing: 10
                    Text {
                        width: parent.width
                        text: folie.titel
                        color: presentation.text
                        wrapMode: Text.WordWrap
                        font { family: "DejaVu Sans"; bold: true; pixelSize: 24 }
                    }
                    Text {
                        width: parent.width
                        text: folie.inhalt
                        color: presentation.leise
                        wrapMode: Text.WordWrap
                        lineHeight: 1.2
                        font { family: "DejaVu Sans"; pixelSize: 15 }
                    }
                }
            }
        }
        Text {
            anchors { horizontalCenter: parent.horizontalCenter; top: kachel.bottom; topMargin: 22 }
            text: "AUF BIBLIX GEHT DAS."
            color: presentation.gelb
            font { family: "DejaVu Sans Mono"; bold: true; pixelSize: 13; letterSpacing: 2 }
        }
    }

    Folie {
        titel: "Biblix wird eingerichtet."
        inhalt: "Lehn dich zurück, der Rest läuft von selbst und dauert ein paar Minuten. Danach startet dein PC neu."
    }
    Folie {
        zeichen: "S"
        titel: "S-Launcher"
        inhalt: "Apps und Spiele mit einem Klick, Steam inklusive. Unter „Hausmarke Bibi“ findest du alles, was Biblix selbst mitbringt."
    }
    Folie {
        zeichen: "◆"
        titel: "Biblix Design"
        inhalt: "Sechs Firmen-Looks von Bibi Tech bis Nassmacher, hell oder dunkel, und alles einzeln mischbar: Fenster, Leiste, Symbole, Klänge."
    }
    Folie {
        zeichen: "▶"
        titel: "Bibiplexx"
        inhalt: "Deine Filme und Serien im eigenen Kino, mit Vorhang, Gong und Weiterschauen. Reihe sieben."
    }
    Folie {
        zeichen: "⟲"
        titel: "Zeitmaschine"
        inhalt: "Vor jedem Update hält Biblix den Zustand fest. Geht etwas schief, drehst du das Update in der Haustechnik einfach zurück."
    }
    Folie {
        zeichen: "⊞"
        titel: "Windows bleibt da."
        inhalt: "Ein Knopf startet Windows, ein Knopf in Windows startet Biblix. Spiele mit Anti-Cheat starten direkt in Windows."
    }

    function onActivate() { }
    function onLeave() { }
}
