/*
    Schrauben-Knopf: Sechskant-Mutter mit Symbol.
    Ruhig: grauer Umriss, Symbol sichtbar. Drüberfahren: füllt sich mit Farbe und dreht sich eine Sechsteldrehung.
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
    signal ausgeloest()

    readonly property color farbe: gefahr ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.highlightColor
    readonly property color ruhe: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.45)
    readonly property bool aktiv: maus.containsMouse

    implicitWidth: Kirigami.Units.gridUnit * 1.9
    implicitHeight: implicitWidth

    Shape {
        id: mutter
        anchors.fill: parent
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
        anchors.centerIn: parent
        width: parent.width * 0.48
        height: width
        source: knopf.symbol
        color: knopf.aktiv ? Kirigami.Theme.highlightedTextColor : Kirigami.Theme.textColor
        isMask: true
        opacity: knopf.aktiv ? 1 : 0.75
    }
    MouseArea {
        id: maus
        anchors.fill: parent
        hoverEnabled: true
        onClicked: knopf.ausgeloest()
    }
    QQC2.ToolTip.text: knopf.tipp
    QQC2.ToolTip.visible: maus.containsMouse
    QQC2.ToolTip.delay: 500
}
