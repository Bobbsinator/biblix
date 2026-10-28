// Eine App in der Fensterleiste. Typenschild: Fassung, LED fuers aktive Fenster, Muttern fuer die Fensterzahl.
// Flache Formen (Drei Zonen, Inseln, Kopfzeile): nur das Symbol, darunter ein Strich je nach Zustand.
import QtQuick
import QtQuick.Effects
import QtQuick.Shapes
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasmoid
import org.kde.kirigami as Kirigami

Item {
    id: kachel
    required property int index
    required property var model
    required property var decoration
    required property string display
    property var leisteRoot
    property real groesse: 44

    readonly property var s: leisteRoot.stil
    readonly property bool aktiv: model.IsActive === true
    readonly property bool starter: model.IsLauncher === true
    readonly property int anzahl: model.IsGroupParent ? model.ChildCount : (model.IsWindow ? 1 : 0)
    readonly property bool ruft: model.IsDemandingAttention === true
    readonly property bool flach: leisteRoot.flach
    // Platz fuer Metallring, Rahmen, Hover-Vergroesserung und die Muttern darunter: nichts darf aus der Leiste ragen
    readonly property real kante: Math.round(groesse * (s.metall ? 0.68 : (s.form === "rund" ? 0.76 : 0.8)))

    width: groesse
    height: groesse

    // Fassung
    Rectangle {
        id: fassung
        width: kachel.kante
        height: kachel.kante
        anchors.centerIn: parent
        anchors.verticalCenterOffset: -Math.round(kachel.groesse * 0.05)
        radius: width * s.radius
        color: kachel.flach ? (maus.containsMouse || kachel.aktiv ? Qt.alpha(leisteRoot.f.text, kachel.aktiv ? 0.07 : 0.1) : "transparent") : s.kachel
        border.width: kachel.flach ? 0 : (kachel.aktiv || maus.containsMouse ? 2 : 1)
        border.color: kachel.aktiv ? s.randAktiv : (maus.containsMouse ? Qt.lighter(s.rand, 1.4) : s.rand)
        scale: maus.pressed ? 0.94 : (maus.containsMouse ? 1.04 : 1.0)
        Behavior on scale { NumberAnimation { duration: 140; easing.type: Easing.OutBack } }
        Behavior on border.color { ColorAnimation { duration: 160 } }

        // Metallring fuer runde Knoepfe (Welt Tower)
        Rectangle {
            visible: s.metall && !kachel.flach
            anchors.fill: parent
            anchors.margins: -Math.max(2, kachel.kante * 0.07)
            z: -1
            radius: width / 2
            gradient: Gradient {
                GradientStop { position: 0; color: "#d6dade" }
                GradientStop { position: 1; color: "#6b717a" }
            }
        }
        // Glanzkante oben
        Rectangle {
            visible: s.form === "kachel" && !kachel.flach
            anchors { left: parent.left; right: parent.right; top: parent.top; margins: parent.radius * 0.6 }
            anchors.topMargin: 1
            height: 1
            color: Qt.rgba(1, 1, 1, 0.08)
        }
        // Wer ruft, blinkt
        SequentialAnimation on border.width {
            running: kachel.ruft && !kachel.flach
            loops: Animation.Infinite
            NumberAnimation { to: 3; duration: 400 }
            NumberAnimation { to: 1; duration: 400 }
        }

        Kirigami.Icon {
            id: symbol
            anchors.centerIn: parent
            width: Math.round(kachel.kante * (s.form === "rund" ? 0.62 : 0.68))
            height: width
            source: kachel.decoration
            visible: !lackEffekt.visible
            opacity: kachel.starter ? 0.92 : 1
        }
        MultiEffect {
            id: lackEffekt
            source: symbol
            anchors.fill: symbol
            visible: leisteRoot.lack && !kachel.aktiv
            colorization: 1.0
            colorizationColor: leisteRoot.f.akzent
            brightness: 0.12
        }
    }

    // Flache Formen: Strich unter offenen Fenstern, breit und in Akzentfarbe beim aktiven
    Rectangle {
        visible: kachel.flach && (kachel.anzahl > 0 || kachel.ruft)
        width: Math.round(kachel.groesse * (kachel.aktiv ? 0.5 : (kachel.anzahl > 1 ? 0.36 : 0.22)))
        height: kachel.aktiv ? 3 : 2
        radius: height / 2
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 1
        color: kachel.ruft ? leisteRoot.f.akzent2 : (kachel.aktiv ? leisteRoot.f.akzent : leisteRoot.f.leise)
        Behavior on width { NumberAnimation { duration: 160; easing.type: Easing.OutCubic } }
        Behavior on color { ColorAnimation { duration: 160 } }
    }

    // LED unter dem aktiven Fenster
    Rectangle {
        visible: kachel.aktiv && !kachel.flach
        width: Math.round(kachel.groesse * 0.36)
        height: width
        radius: width / 2
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.bottom
        anchors.verticalCenterOffset: -2
        gradient: Gradient {
            orientation: Gradient.Horizontal
            GradientStop { position: 0.0; color: "transparent" }
            GradientStop { position: 0.5; color: Qt.alpha(s.led, 0.55) }
            GradientStop { position: 1.0; color: "transparent" }
        }
    }
    // Muttern: eine je offenem Fenster (hoechstens vier)
    Row {
        visible: !kachel.flach
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 0
        spacing: Math.max(2, kachel.groesse * 0.06)
        Repeater {
            model: Math.min(4, kachel.anzahl)
            Shape {
                width: Math.max(5, kachel.groesse * 0.13)
                height: width
                preferredRendererType: Shape.CurveRenderer
                ShapePath {
                    strokeWidth: 0
                    fillColor: kachel.aktiv ? s.led : Qt.alpha(leisteRoot.f.text, 0.55)
                    PathPolyline {
                        path: {
                            const r = width / 2, p = [];
                            for (let i = 0; i <= 6; i++) {
                                const a = Math.PI / 3 * i + Math.PI / 6;
                                p.push(Qt.point(r + r * Math.cos(a), r + r * Math.sin(a)));
                            }
                            return p;
                        }
                    }
                }
            }
        }
    }

    // Fortschritt (z. B. Downloads), wenn die App ihn meldet; Delivery zeigt die Statuskette
    Loader {
        id: fortschrittLader
        source: "Fortschritt.qml"
        onLoaded: item.launcherUrl = Qt.binding(() => kachel.model.LauncherUrlWithoutIcon)
    }
    Item {
        readonly property bool zeigen: fortschrittLader.item && fortschrittLader.item.sichtbar
        readonly property real wert: zeigen ? fortschrittLader.item.wert : 0
        visible: zeigen
        anchors.fill: fassung
        Rectangle {
            visible: leisteRoot.welt !== "delivery"
            anchors { left: parent.left; bottom: parent.bottom; margins: 4 }
            height: 3
            width: (parent.width - 8) * parent.wert
            radius: 1.5
            color: s.led
        }
        Row {
            visible: leisteRoot.welt === "delivery"
            anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 3 }
            spacing: 2
            Repeater {
                model: 6
                Rectangle {
                    required property int index
                    width: 4; height: 4; radius: 2
                    color: index / 5 <= parent.parent.wert ? "#ffd400" : "#2b50c8"
                }
            }
        }
    }

    PlasmaCore.ToolTipArea {
        anchors.fill: parent
        mainText: kachel.model.AppName || kachel.display
        subText: kachel.starter ? "Starten" : (kachel.anzahl > 1 ? kachel.anzahl + " Fenster" : kachel.display)
        location: Plasmoid.location
    }
    MouseArea {
        id: maus
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.LeftButton | Qt.MiddleButton | Qt.RightButton
        onClicked: mouse => {
            if (mouse.button === Qt.MiddleButton) {
                leisteRoot.neuesFenster(kachel.index);
            } else if (mouse.button === Qt.RightButton) {
                const url = kachel.model.LauncherUrlWithoutIcon;
                const hatUrl = !!url && url.toString().length > 0;
                leisteRoot.menueZeigen(kachel, kachel.index, {
                    url: hatUrl ? url : "",
                    angeheftet: hatUrl ? leisteRoot.angeheftet(url) : false,
                    anzahl: kachel.anzahl
                });
            } else {
                leisteRoot.klick(kachel.index, kachel.model);
            }
        }
    }
}
