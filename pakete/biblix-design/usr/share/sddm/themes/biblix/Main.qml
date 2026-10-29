/*
    Biblix-Anmeldung (SDDM, Theme-API 2): Standort-Hintergrund des aktuellen Designs, Karte mit blauem B,
    Passwortzeile im Terminal-Stil, Uhr oben rechts, Sitzung und Ausschalten unten.
    Farben und Hintergrund schreibt Biblix Design nach theme.conf.user (biblix-design-system).
    Nur QtQuick, keine weiteren Module: faellt hier etwas aus, nimmt SDDM sein eingebautes Thema.
*/
import QtQuick

Rectangle {
    id: wurzel
    width: 1920
    height: 1080
    color: config.grund || "#0f141c"

    readonly property color grund: config.grund || "#0f141c"
    readonly property color karte: config.karte || "#1a2029"
    readonly property color rand: config.rand || "#313a48"
    readonly property color text: config.text || "#e8ecf2"
    readonly property color leise: config.leise || "#8b95a5"
    readonly property color akzent: config.akzent || "#378add"
    readonly property color gefahr: config.gefahr || "#e24b4a"
    readonly property string spruch: config.spruch || "AUF BIBLIX GEHT DAS."
    readonly property real s: Math.max(0.6, Math.min(width / 1920, height / 1080))   // Skala fuer kleine Bildschirme
    readonly property var de: Qt.locale("de_DE")

    property int benutzer: userModel.lastIndex >= 0 ? userModel.lastIndex : 0
    property int sitzung: sessionModel.lastIndex >= 0 ? sessionModel.lastIndex : 0
    property bool arbeitet: false
    property string meldung: ""

    // Namen aus den Modellen lesen (die Modelle haben keine get()-Funktion)
    Repeater { id: benutzerListe; model: userModel
        delegate: Item { required property string name; required property string realName; required property string icon } }
    Repeater { id: sitzungsListe; model: sessionModel
        delegate: Item { required property string name } }
    readonly property var aktuell: benutzerListe.count > 0 ? benutzerListe.itemAt(Math.min(benutzer, benutzerListe.count - 1)) : null
    readonly property string anmeldeName: aktuell ? aktuell.name : ""
    readonly property string anzeigeName: aktuell ? (aktuell.realName || aktuell.name) : ""
    readonly property string sitzungsName: sitzungsListe.count > 0 && sitzungsListe.itemAt(sitzung) ? sitzungsListe.itemAt(sitzung).name : ""

    function anmelden() {
        if (arbeitet || anmeldeName === "")
            return;
        arbeitet = true;
        meldung = "";
        sddm.login(anmeldeName, passwort.text, sitzung);
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            wurzel.arbeitet = false;
            wurzel.meldung = "Das war nicht das Passwort.";
            passwort.text = "";
            wackeln.restart();
            passwort.forceActiveFocus();
        }
        function onLoginSucceeded() {
            wurzel.meldung = "";
        }
    }

    // ------------------------------------------------------------ Hintergrund
    Image {
        anchors.fill: parent
        source: config.background ? "file://" + config.background : ""
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        smooth: true
    }
    Rectangle {   // leicht abdunkeln, damit Karte und Uhr lesbar bleiben
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: Qt.rgba(0, 0, 0, 0.15) }
            GradientStop { position: 0.6; color: Qt.rgba(0, 0, 0, 0.35) }
            GradientStop { position: 1.0; color: Qt.rgba(0, 0, 0, 0.6) }
        }
    }

    // ------------------------------------------------------------ Uhr oben links, auf eigener Tafel
    // (die Standort-Bilder haben oben rechts oft ihr Typenschild)
    property date jetzt: new Date()
    Timer { interval: 1000; running: true; repeat: true; onTriggered: wurzel.jetzt = new Date() }
    Rectangle {
        anchors { left: parent.left; top: parent.top; margins: 40 * wurzel.s }
        width: uhrSpalte.width + 48 * wurzel.s
        height: uhrSpalte.height + 32 * wurzel.s
        radius: 18 * wurzel.s
        color: Qt.alpha(wurzel.karte, 0.85)
        border.width: 1
        border.color: wurzel.rand
    }
    Column {
        id: uhrSpalte
        anchors { left: parent.left; top: parent.top; leftMargin: 64 * wurzel.s; topMargin: 56 * wurzel.s }
        spacing: 2 * wurzel.s
        Text {
            anchors.left: parent.left
            text: Qt.formatTime(wurzel.jetzt, "hh:mm")
            color: wurzel.text
            font { family: "DejaVu Sans Mono"; bold: true; pixelSize: 60 * wurzel.s }
        }
        Text {
            anchors.left: parent.left
            text: wurzel.de.toString(wurzel.jetzt, "dddd, d. MMMM")
            color: wurzel.leise
            font { family: "DejaVu Sans"; pixelSize: 20 * wurzel.s }
        }
    }

    // ------------------------------------------------------------ Anmeldekarte
    Rectangle {
        id: kartenFlaeche
        width: 440 * wurzel.s
        height: inhalt.height + 64 * wurzel.s
        anchors.centerIn: parent
        anchors.verticalCenterOffset: 40 * wurzel.s
        radius: 22 * wurzel.s
        color: Qt.alpha(wurzel.karte, 0.92)
        border.width: 1
        border.color: wurzel.rand

        // Wackeln bei falschem Passwort
        transform: Translate { id: versatz }
        SequentialAnimation {
            id: wackeln
            loops: 2
            NumberAnimation { target: versatz; property: "x"; to: -14 * wurzel.s; duration: 50 }
            NumberAnimation { target: versatz; property: "x"; to: 14 * wurzel.s; duration: 80 }
            NumberAnimation { target: versatz; property: "x"; to: 0; duration: 50 }
        }

        Column {
            id: inhalt
            anchors { top: parent.top; topMargin: 36 * wurzel.s; horizontalCenter: parent.horizontalCenter }
            width: parent.width - 64 * wurzel.s
            spacing: 18 * wurzel.s

            // Blaues B
            Rectangle {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 88 * wurzel.s
                height: width
                radius: width * 0.24
                color: "#378add"
                Text {
                    anchors.centerIn: parent
                    anchors.horizontalCenterOffset: 2 * wurzel.s
                    text: "B"
                    color: "#ffffff"
                    font { family: "DejaVu Sans"; bold: true; pixelSize: parent.height * 0.6 }
                }
            }

            // Name, bei mehreren Benutzern mit Pfeilen zum Wechseln
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 14 * wurzel.s
                Text {
                    visible: benutzerListe.count > 1
                    text: "‹"
                    color: zurueckMaus.containsMouse ? wurzel.akzent : wurzel.leise
                    font.pixelSize: 30 * wurzel.s
                    anchors.verticalCenter: parent.verticalCenter
                    MouseArea { id: zurueckMaus; anchors.fill: parent; anchors.margins: -10; hoverEnabled: true
                        onClicked: wurzel.benutzer = (wurzel.benutzer + benutzerListe.count - 1) % benutzerListe.count }
                }
                Text {
                    text: wurzel.anzeigeName
                    color: wurzel.text
                    font { family: "DejaVu Sans"; bold: true; pixelSize: 26 * wurzel.s }
                }
                Text {
                    visible: benutzerListe.count > 1
                    text: "›"
                    color: weiterMaus.containsMouse ? wurzel.akzent : wurzel.leise
                    font.pixelSize: 30 * wurzel.s
                    anchors.verticalCenter: parent.verticalCenter
                    MouseArea { id: weiterMaus; anchors.fill: parent; anchors.margins: -10; hoverEnabled: true
                        onClicked: wurzel.benutzer = (wurzel.benutzer + 1) % benutzerListe.count }
                }
            }

            // Passwortzeile im Terminal-Stil
            Rectangle {
                width: parent.width
                height: 56 * wurzel.s
                radius: 12 * wurzel.s
                color: Qt.darker(wurzel.grund, 1.2)
                border.width: passwort.activeFocus ? 2 : 1
                border.color: wurzel.meldung !== "" ? wurzel.gefahr : (passwort.activeFocus ? wurzel.akzent : wurzel.rand)
                Behavior on border.color { ColorAnimation { duration: 160 } }

                Text {
                    id: prompt
                    anchors { left: parent.left; leftMargin: 18 * wurzel.s; verticalCenter: parent.verticalCenter }
                    text: "passwort>"
                    color: wurzel.akzent
                    font { family: "DejaVu Sans Mono"; bold: true; pixelSize: 18 * wurzel.s }
                }
                TextInput {
                    id: passwort
                    anchors { left: prompt.right; leftMargin: 12 * wurzel.s; right: los.left; rightMargin: 10 * wurzel.s
                              verticalCenter: parent.verticalCenter }
                    echoMode: TextInput.Password
                    passwordCharacter: "•"
                    color: wurzel.text
                    selectionColor: wurzel.akzent
                    font { family: "DejaVu Sans Mono"; pixelSize: 20 * wurzel.s }
                    cursorDelegate: Item {}   // eigener Block-Cursor statt des duennen Strichs
                    focus: true
                    clip: true
                    enabled: !wurzel.arbeitet
                    onAccepted: wurzel.anmelden()
                    onTextChanged: if (text !== "") wurzel.meldung = ""
                    Keys.onEscapePressed: text = ""
                    // eigener Block-Cursor wie im Terminal
                    Rectangle {
                        x: passwort.cursorRectangle.x + 2
                        anchors.verticalCenter: parent.verticalCenter
                        width: 11 * wurzel.s
                        height: 22 * wurzel.s
                        color: wurzel.akzent
                        visible: passwort.activeFocus && blinken.an
                    }
                }
                Timer { id: blinken; property bool an: true; interval: 530; running: true; repeat: true; onTriggered: an = !an }

                // Anmelden-Knopf
                Rectangle {
                    id: los
                    anchors { right: parent.right; rightMargin: 8 * wurzel.s; verticalCenter: parent.verticalCenter }
                    width: 40 * wurzel.s
                    height: width
                    radius: 9 * wurzel.s
                    color: losMaus.containsMouse ? Qt.lighter(wurzel.akzent, 1.15) : wurzel.akzent
                    Text {
                        anchors.centerIn: parent
                        text: wurzel.arbeitet ? "…" : "→"
                        color: "#ffffff"
                        font { family: "DejaVu Sans"; bold: true; pixelSize: 20 * wurzel.s }
                    }
                    MouseArea { id: losMaus; anchors.fill: parent; hoverEnabled: true; onClicked: wurzel.anmelden() }
                }
            }

            // Meldung bei Fehler, sonst der Spruch
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: wurzel.meldung !== "" ? wurzel.meldung : (keyboard.capsLock ? "Feststelltaste ist an." : wurzel.spruch)
                color: wurzel.meldung !== "" ? wurzel.gefahr : (keyboard.capsLock ? wurzel.akzent : wurzel.leise)
                font { family: "DejaVu Sans Mono"; pixelSize: 14 * wurzel.s; letterSpacing: 1 }
            }
        }
    }

    // ------------------------------------------------------------ Leiste unten: Sitzung und Ausschalten
    component Knopf: Rectangle {
        id: k
        property string beschriftung
        property string zeichen
        property bool warnung: false
        signal ausgeloest
        height: 44 * wurzel.s
        width: zeile.width + 32 * wurzel.s
        radius: 12 * wurzel.s
        color: km.containsMouse ? Qt.alpha(warnung ? wurzel.gefahr : wurzel.akzent, 0.85) : Qt.alpha(wurzel.karte, 0.85)
        border.width: 1
        border.color: wurzel.rand
        Behavior on color { ColorAnimation { duration: 120 } }
        Row {
            id: zeile
            anchors.centerIn: parent
            spacing: 10 * wurzel.s
            Text { text: k.zeichen; color: wurzel.text; font.pixelSize: 18 * wurzel.s; anchors.verticalCenter: parent.verticalCenter }
            Text { text: k.beschriftung; color: wurzel.text; font { family: "DejaVu Sans"; pixelSize: 16 * wurzel.s }
                   anchors.verticalCenter: parent.verticalCenter }
        }
        MouseArea { id: km; anchors.fill: parent; hoverEnabled: true; onClicked: k.ausgeloest() }
    }

    Row {
        anchors { left: parent.left; bottom: parent.bottom; margins: 40 * wurzel.s }
        spacing: 12 * wurzel.s
        Knopf {
            visible: sitzungsListe.count > 1
            zeichen: "▤"
            beschriftung: "Sitzung: " + wurzel.sitzungsName
            onAusgeloest: wurzel.sitzung = (wurzel.sitzung + 1) % sitzungsListe.count
        }
    }
    Row {
        anchors { right: parent.right; bottom: parent.bottom; margins: 40 * wurzel.s }
        spacing: 12 * wurzel.s
        Knopf { visible: sddm.canSuspend; zeichen: "☾"; beschriftung: "Ruhezustand"; onAusgeloest: sddm.suspend() }
        Knopf { visible: sddm.canReboot; zeichen: "↻"; beschriftung: "Neustart"; onAusgeloest: sddm.reboot() }
        Knopf { visible: sddm.canPowerOff; zeichen: "⏻"; beschriftung: "Ausschalten"; warnung: true; onAusgeloest: sddm.powerOff() }
    }

    Component.onCompleted: passwort.forceActiveFocus()
}
