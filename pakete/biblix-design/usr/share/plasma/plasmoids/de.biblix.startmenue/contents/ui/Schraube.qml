/*
    Schrauben-Knopf: Sechskant-Mutter mit Symbol.
    Ruhig: grauer Umriss, Symbol sichtbar. Drüberfahren: füllt sich mit Farbe und dreht sich eine Sechsteldrehung.
    Mit „beschriftung“ steht der Name klein darunter (Fuß des Startmenüs).
*/
import QtQuick
import QtQuick.Shapes
import QtQuick.Controls as QQC2
import org.kde.plasma.components as PC3
import org.kde.kirigami as Kirigami

Item {
    id: knopf
    property string symbol
    property string tipp
    property bool gefahr: false
    property string beschriftung: ""
    signal ausgeloest()

    readonly property color farbe: gefahr ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.highlightColor
    readonly property color ruhe: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.45)
    readonly property bool aktiv: maus.containsMouse

    readonly property real seite: Kirigami.Units.gridUnit * 1.9
    implicitWidth: beschriftung ? Math.max(seite, name.implicitWidth) : seite
    implicitHeight: beschriftung ? seite + name.implicitHeight + 2 : seite

    Shape {
        id: mutter
        width: knopf.seite
        height: knopf.seite
        anchors.horizontalCenter: parent.horizontalCenter
        rotation: knopf.aktiv ? 30 : 0
        scale: maus.pressed ? 0.9 : 1
        Behavior on rotation { NumberAnimation { duration: 260; easing.type: Easing.OutBack; easing.overshoot: 2 } }
        Behavior on scale { NumberAnimation { duration: 120 } }
        preferredRendererType: Shape.CurveRenderer
        ShapePath {
            strokeColor: knopf.aktiv ? knopf.farbe : knopf.ruhe
            strokeWidth: 1.6
            fillColor: knopf.aktiv ? (maus.pressed ? Qt.darker(knopf.farbe, 1.25) : knopf.farbe) : "transparent"
            joinStyle: ShapePath.RoundJoin
            Behavior on fillColor { ColorAnimation { duration: 140 } }
            readonly property real w: mutter.width
            readonly property real h: mutter.height
            startX: w * 0.5; startY: h * 0.05
            PathLine { x: mutter.width * 0.9; y: mutter.height * 0.275 }
            PathLine { x: mutter.width * 0.9; y: mutter.height * 0.725 }
            PathLine { x: mutter.width * 0.5; y: mutter.height * 0.95 }
            PathLine { x: mutter.width * 0.1; y: mutter.height * 0.725 }
            PathLine { x: mutter.width * 0.1; y: mutter.height * 0.275 }
            PathLine { x: mutter.width * 0.5; y: mutter.height * 0.05 }
        }
    }
    Kirigami.Icon {
        anchors.centerIn: mutter
        width: knopf.seite * 0.48
        height: width
        source: knopf.symbol
        color: knopf.aktiv ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
        isMask: true
        opacity: knopf.aktiv ? 1 : 0.75
    }
    PC3.Label {
        id: name
        visible: knopf.beschriftung !== ""
        anchors { top: mutter.bottom; topMargin: 2; horizontalCenter: parent.horizontalCenter }
        text: knopf.beschriftung
        font.pixelSize: Kirigami.Units.gridUnit * 0.55
        color: knopf.aktiv ? knopf.farbe : Kirigami.Theme.textColor
        opacity: knopf.aktiv ? 1 : 0.65
    }
    MouseArea {
        id: maus
        anchors.fill: parent
        hoverEnabled: true
        onClicked: knopf.ausgeloest()
    }
    QQC2.ToolTip.text: knopf.tipp
    QQC2.ToolTip.visible: maus.containsMouse && knopf.beschriftung === ""
    QQC2.ToolTip.delay: 500
}
