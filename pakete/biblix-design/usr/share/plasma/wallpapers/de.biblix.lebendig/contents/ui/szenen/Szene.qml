// Grundlage aller Szenen: Farben (f), laeuft (Pause), tempo und Hilfen
import QtQuick

Item {
    id: basis
    property var f: ({})
    property bool laeuft: true
    property real tempo: 1.0
    property var sprueche: []
    clip: true

    // Farbe aus der Palette, optional mit Deckkraft
    function c(name, alpha) {
        const col = Qt.color(f[name] || "#888888");
        return alpha === undefined ? col : Qt.rgba(col.r, col.g, col.b, alpha);
    }
    // Zwischenfarbe a->b (t = 0..1)
    function mix(a, b, t, alpha) {
        const x = Qt.color(f[a] || a), y = Qt.color(f[b] || b);
        return Qt.rgba(x.r + (y.r - x.r) * t, x.g + (y.g - x.g) * t, x.b + (y.b - x.b) * t, alpha === undefined ? 1 : alpha);
    }
    // Wiederholbarer Zufall (gleiche Szene sieht nach dem Neustart gleich aus)
    function zufall(i) {
        const x = Math.sin(i * 12.9898 + 78.233) * 43758.5453;
        return x - Math.floor(x);
    }
}
