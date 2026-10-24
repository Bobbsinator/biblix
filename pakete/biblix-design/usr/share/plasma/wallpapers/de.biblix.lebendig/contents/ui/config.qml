// Einstellungen in "Hintergrundbild einrichten" (Rechtsklick auf den Desktop).
// Farben und Sprüche setzt Biblix Design; hier nur Szene, Tempo und Pause.
import QtQuick
import QtQuick.Controls as QQC2
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    id: seite
    property string cfg_Szene
    property alias cfg_Tempo: tempo.value
    property alias cfg_Pausieren: pause.checked

    readonly property var szenen: [
        ["sternenflug", "Sternenflug"], ["sternenhimmel", "Sternenhimmel"], ["gluehwuermchen", "Glühwürmchen"],
        ["schnee", "Schnee"], ["regen", "Regen"], ["bokeh", "Bokeh"], ["farbnebel", "Farbnebel"],
        ["wellen", "Wellen"], ["tropfen", "Tropfen"], ["muttern", "Schwebende Muttern"], ["waben", "Leuchtwaben"],
        ["tunnel", "Muttern-Tunnel"], ["platine", "Stromkreis"], ["equalizer", "Equalizer"], ["synthwave", "Synthwave"],
        ["prompt", "Prompt mit Bibi-Sprüchen"], ["bauplan", "Bauplan"], ["tower", "Tower bei Nacht"],
        ["wafer", "Wafer unterm Laser"], ["kurse", "Zugriffsindex"], ["route", "Route"], ["boegen", "Lächelbögen"],
        ["donau", "Donau-Abend"], ["saal", "Saallichter"]
    ]

    QQC2.ComboBox {
        Kirigami.FormData.label: "Szene:"
        model: seite.szenen.map(s => s[1])
        currentIndex: Math.max(0, seite.szenen.findIndex(s => s[0] === seite.cfg_Szene))
        onActivated: index => seite.cfg_Szene = seite.szenen[index][0]
    }
    QQC2.Slider {
        id: tempo
        Kirigami.FormData.label: "Tempo:"
        from: 0.3; to: 2.0; stepSize: 0.1
    }
    QQC2.CheckBox {
        id: pause
        Kirigami.FormData.label: "Leistung:"
        text: "Pausieren bei Vollbild und maximierten Fenstern"
    }
    QQC2.Label {
        text: "Farben kommen aus Biblix Design. Dort gibt es auch Vorschaubilder."
        opacity: 0.7
    }
}
