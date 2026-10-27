/*
    Biblix-Instrumentenfeld: steht in der Leiste direkt vor den Symbolen unten rechts (Systemabschnitt)
    und zeichnet darunter eine eingelassene Fassung, so breit wie der Nachbar rechts davon.
    Der Systemabschnitt selbst bleibt der von KDE und wird nicht veraendert.
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: feld

    preferredRepresentation: fullRepresentation
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground

    readonly property var standard: ({ grund: "#0f141c", flaeche: "#1a2029", karte: "#232a35", rand: "#313a48", text: "#e8ecf2", akzent: "#378add", akzent2: "#ffd400" })
    readonly property var f: {
        let x = {};
        try { x = JSON.parse(Plasmoid.configuration.farben || "{}"); } catch (e) { x = {}; }
        return Object.assign({}, standard, x);
    }
    readonly property var stil: {
        const w = {
            typenschild: { fuellung: Qt.darker(f.grund, 1.35), rand: f.rand, licht: Qt.rgba(1, 1, 1, 0.07), radius: 0.32, schrauben: true, lampen: false },
            tower:       { fuellung: "#0b0d10", rand: "#8b9098", licht: Qt.rgba(1, 1, 1, 0.12), radius: 0.2, schrauben: true, lampen: false },
            bank:        { fuellung: "#0c2219", rand: "#c9a227", licht: Qt.rgba(1, 0.9, 0.6, 0.12), radius: 0.12, schrauben: true, lampen: false },
            mac:         { fuellung: "#2a0d0a", rand: "#ffc72c", licht: Qt.rgba(1, 1, 1, 0.08), radius: 0.5, schrauben: false, lampen: false },
            delivery:    { fuellung: "#071548", rand: "#2b50c8", licht: Qt.rgba(1, 0.85, 0, 0.35), radius: 0.24, schrauben: false, lampen: false },
            plexx:       { fuellung: "#0d0718", rand: "#ff8a3d", licht: Qt.rgba(1, 1, 1, 0.05), radius: 0.16, schrauben: false, lampen: true },
            nass:        { fuellung: "#04262c", rand: "#22d3e6", licht: Qt.rgba(1, 1, 1, 0.18), radius: 0.5, schrauben: false, lampen: false }
        };
        return w[Plasmoid.configuration.welt] || w.typenschild;
    }

    fullRepresentation: Item {
        id: halter
        readonly property real rand: Kirigami.Units.smallSpacing * 2
        Layout.minimumWidth: rand
        Layout.preferredWidth: rand
        Layout.maximumWidth: rand
        Layout.fillHeight: true

        // Unser Platz in der Leiste und der rechte Nachbar (der Systemabschnitt)
        readonly property Item platz: feld.parent
        property Item nachbar: null
        function suchen() {
            if (!platz || !platz.parent) return;
            platz.z = -1;   // unter den Nachbarn zeichnen
            let bester = null;
            for (const k of platz.parent.children) {
                if (k === platz || !k.visible || k.width <= 0) continue;
                if (k.x >= platz.x + platz.width - 1 && (!bester || k.x < bester.x)) bester = k;
            }
            nachbar = bester;
        }
        Component.onCompleted: Qt.callLater(suchen)
        Timer { interval: 2000; running: true; repeat: true; onTriggered: halter.suchen() }

        Rectangle {
            id: fassung
            readonly property real hoehe: halter.height - Kirigami.Units.smallSpacing * 2
            x: Math.round(halter.rand * 0.25)
            y: Math.round((halter.height - hoehe) / 2)
            height: hoehe
            width: halter.nachbar ? halter.nachbar.x + halter.nachbar.width - halter.platz.x - x + halter.rand * 0.75 : halter.width
            radius: Math.min(height / 2, height * feld.stil.radius * 2)
            color: feld.stil.fuellung
            border.width: 1
            border.color: feld.stil.rand
            // eingelassen: dunkle Kante oben, Licht unten
            Rectangle { anchors { left: parent.left; right: parent.right; top: parent.top; margins: parent.radius * 0.5 } anchors.topMargin: 1
                        height: 2; color: Qt.rgba(0, 0, 0, 0.35) }
            Rectangle { anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: parent.radius * 0.5 } anchors.bottomMargin: 1
                        height: 1; color: feld.stil.licht }
            // Schrauben an den Enden
            Repeater {
                model: feld.stil.schrauben ? 2 : 0
                Rectangle {
                    required property int index
                    width: 4; height: 4; radius: 2
                    x: index === 0 ? 3 : fassung.width - 7
                    y: (fassung.height - height) / 2
                    color: "#9aa1ab"
                    border.width: 1; border.color: "#2a2e35"
                }
            }
            // Kinolichter oben (Bibiplexx)
            Repeater {
                model: feld.stil.lampen ? Math.floor(fassung.width / 10) : 0
                Rectangle {
                    required property int index
                    x: 6 + index * 10; y: 2; width: 3; height: 3; radius: 1.5
                    color: index % 2 ? "#ffd27a" : "#7a4a20"
                }
            }
        }
    }
}
