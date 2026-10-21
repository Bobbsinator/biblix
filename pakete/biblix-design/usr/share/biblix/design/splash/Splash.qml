/*
    Biblix-Startbildschirm nach der Anmeldung (KSplash).
    Vorlage: Biblix Design setzt Farben und Stil ein (@...@).
    Stile: tippen (Prompt-B tippt "AUF BIBLIX GEHT DAS."), schrauben (Schrauben-B dreht sich fest), einblenden
*/
import QtQuick

Rectangle {
    id: root
    color: "@GRUND@"

    property int stage
    readonly property string stil: "@STIL@"
    readonly property string satz: "AUF BIBLIX GEHT DAS."
    property int getippt: 0

    onStageChanged: {
        if (stage == 5) {
            ende.start();
        }
    }
    Component.onCompleted: anfang.start()

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: "@FLAECHE@" }
            GradientStop { position: 1.0; color: "@GRUND@" }
        }
    }

    Item {
        id: inhalt
        anchors.centerIn: parent
        width: 420
        height: 340
        opacity: 0
        scale: 0.92

        // --- Prompt-B tippt
        Image {
            id: logo
            visible: root.stil !== "schrauben"
            anchors.horizontalCenter: parent.horizontalCenter
            y: 0
            width: 200
            height: 200
            sourceSize.width: 400
            sourceSize.height: 400
            source: "images/logo.svg"
        }
        Rectangle {
            id: cursor
            visible: root.stil !== "schrauben"
            color: "@AKZENT@"
            radius: 3
            x: logo.x + 200 * 54 / 120
            y: logo.y + 200 * 94 / 120
            width: 200 * 34 / 120
            height: 200 * 6 / 120
            SequentialAnimation on opacity {
                loops: Animation.Infinite
                running: root.stil === "tippen"
                NumberAnimation { to: 0; duration: 380 }
                NumberAnimation { to: 1; duration: 380 }
            }
        }
        Text {
            id: zeile
            visible: root.stil === "tippen"
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: logo.bottom
            anchors.topMargin: 40
            text: root.satz.substring(0, root.getippt) + (root.getippt < root.satz.length ? "_" : "")
            color: "@TEXT@"
            font.family: "DejaVu Sans Mono"
            font.bold: true
            font.pixelSize: 28
            font.letterSpacing: 2
        }
        Timer {
            running: root.stil === "tippen" && inhalt.opacity > 0.95
            interval: 55
            repeat: true
            onTriggered: if (root.getippt < root.satz.length) root.getippt++
        }

        // --- Schrauben-B dreht sich fest
        Image {
            id: mutter
            visible: root.stil === "schrauben"
            anchors.horizontalCenter: parent.horizontalCenter
            width: 220
            height: 220
            sourceSize.width: 440
            sourceSize.height: 440
            source: "images/mutter.svg"
            rotation: -150
            NumberAnimation on rotation {
                running: root.stil === "schrauben"
                to: 0
                duration: 1400
                easing.type: Easing.OutBack
                easing.overshoot: 1.6
            }
        }
        Text {
            visible: root.stil === "schrauben"
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: mutter.bottom
            anchors.topMargin: 40
            text: root.satz
            color: "@LEISE@"
            font.family: "DejaVu Sans Mono"
            font.bold: true
            font.pixelSize: 24
            font.letterSpacing: 3
        }
    }

    ParallelAnimation {
        id: anfang
        NumberAnimation { target: inhalt; property: "opacity"; to: 1; duration: 500; easing.type: Easing.OutCubic }
        NumberAnimation { target: inhalt; property: "scale"; to: 1; duration: 600; easing.type: Easing.OutBack }
    }
    ParallelAnimation {
        id: ende
        NumberAnimation { target: inhalt; property: "opacity"; to: 0; duration: 350; easing.type: Easing.InCubic }
        NumberAnimation { target: inhalt; property: "scale"; to: 1.12; duration: 350; easing.type: Easing.InCubic }
    }
}
