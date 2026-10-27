/*
    Bibi-Startmenü: der Inhalt (im Panel-Popup und im Vollbild gleich).
*/
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.plasma.plasmoid
import org.kde.plasma.components as PC3
import org.kde.plasma.private.sessions as Sessions
import org.kde.ksysguard.sensors as Sensors
import org.kde.coreaddons as KCoreAddons
import org.kde.kirigami as Kirigami

Item {
    id: inhalt

    required property var wurzel
    property bool gross: false
    property bool offen: wurzel.expanded
    property bool alleApps: false

    readonly property real gu: Kirigami.Units.gridUnit
    readonly property color akzent: Kirigami.Theme.highlightColor
    readonly property color akzent2: Kirigami.Theme.neutralTextColor
    readonly property color karte: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.06)
    readonly property color karteHover: Qt.rgba(akzent.r, akzent.g, akzent.b, 0.22)
    readonly property int spalten: gross ? 8 : 6

    Layout.minimumWidth: gu * 30
    Layout.preferredWidth: gu * 32
    Layout.minimumHeight: gu * 36
    Layout.preferredHeight: gu * 38

    Kirigami.Theme.colorSet: Kirigami.Theme.View
    Kirigami.Theme.inherit: false

    KCoreAddons.KUser { id: nutzer }
    Sessions.SessionManagement { id: sitzung }

    Sensors.Sensor { id: cpuTemp; sensorId: "cpu/all/averageTemperature"; updateRateLimit: 2000 }
    Sensors.Sensor { id: gpuTemp0; sensorId: "gpu/gpu0/temperature"; updateRateLimit: 2000 }
    Sensors.Sensor { id: gpuTemp1; sensorId: "gpu/gpu1/temperature"; updateRateLimit: 2000 }

    property string spruch: "AUF BIBLIX GEHT DAS."
    function neuerSpruch() {
        const s = wurzel.sprueche;
        spruch = s[Math.floor(Math.random() * s.length)];
    }

    // „Bibi-Pop“ beim Öffnen
    onOffenChanged: {
        if (offen) {
            alleApps = false;
            suche.text = "";
            wurzel.aktualisieren();
            neuerSpruch();
            pop.restart();
            suche.forceActiveFocus();
        }
    }
    ParallelAnimation {
        id: pop
        NumberAnimation { target: rahmen; property: "scale"; from: 0.93; to: 1; duration: 280; easing.type: Easing.OutBack; easing.overshoot: 1.7 }
        NumberAnimation { target: rahmen; property: "opacity"; from: 0; to: 1; duration: 180; easing.type: Easing.OutCubic }
        NumberAnimation { target: rahmen; property: "anchors.topMargin"; from: inhalt.gu * 1.4; to: 0; duration: 280; easing.type: Easing.OutCubic }
    }

    Timer {
        id: uhr
        interval: 10000
        running: inhalt.offen
        repeat: true
        triggeredOnStart: true
        property date jetzt: new Date()
        onTriggered: jetzt = new Date()
    }

    Item {
        id: rahmen
        anchors.fill: parent
        anchors.margins: inhalt.gross ? inhalt.gu : 0

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: inhalt.gu * 0.6
            spacing: inhalt.gu * 0.7

            // ------------------------------------------------ Kopf
            RowLayout {
                Layout.fillWidth: true
                spacing: inhalt.gu * 0.6
                Rectangle {
                    Layout.preferredWidth: inhalt.gu * 2.6
                    Layout.preferredHeight: inhalt.gu * 2.6
                    radius: inhalt.gu * 0.6
                    color: inhalt.karte
                    Kirigami.Icon {
                        anchors.fill: parent
                        source: "biblix"
                    }
                }
                ColumnLayout {
                    spacing: 0
                    Layout.fillWidth: true
                    PC3.Label {
                        text: "Hallo, " + (nutzer.fullName || nutzer.loginName)
                        font.weight: Font.Bold
                        font.pixelSize: inhalt.gu * (inhalt.gross ? 1.4 : 1.0)
                        elide: Text.ElideRight
                        Layout.fillWidth: true
                    }
                    PC3.Label {
                        text: uhr.jetzt.toLocaleString(Qt.locale("de_AT"), "dddd, d. MMMM · HH:mm")
                        opacity: 0.65
                        font.pixelSize: inhalt.gu * 0.75
                    }
                }
                // Temperaturen
                Repeater {
                    model: [
                        { name: "CPU", wert: cpuTemp.value },
                        { name: "GPU", wert: Math.max(gpuTemp0.value || 0, gpuTemp1.value || 0) }
                    ]
                    delegate: Rectangle {
                        required property var modelData
                        visible: modelData.wert > 0
                        radius: height / 2
                        implicitHeight: inhalt.gu * 1.4
                        implicitWidth: tempText.implicitWidth + inhalt.gu
                        color: modelData.wert >= 85 ? Qt.rgba(1, 0.3, 0.3, 0.25) : (modelData.wert >= 70 ? Qt.rgba(1, 0.75, 0.2, 0.22) : inhalt.karte)
                        PC3.Label {
                            id: tempText
                            anchors.centerIn: parent
                            text: modelData.name + " " + Math.round(modelData.wert) + "°"
                            font.pixelSize: inhalt.gu * 0.7
                            font.family: "DejaVu Sans Mono"
                        }
                    }
                }
                Rectangle {
                    visible: wurzel.designName !== ""
                    radius: inhalt.gu * 0.3
                    implicitHeight: inhalt.gu * 1.4
                    implicitWidth: designText.implicitWidth + inhalt.gu
                    color: "transparent"
                    border.color: Qt.rgba(inhalt.akzent.r, inhalt.akzent.g, inhalt.akzent.b, 0.6)
                    PC3.Label {
                        id: designText
                        anchors.centerIn: parent
                        text: wurzel.designName
                        color: inhalt.akzent
                        font.pixelSize: inhalt.gu * 0.65
                    }
                }
            }

            // ------------------------------------------------ Suche
            PC3.TextField {
                id: suche
                Layout.fillWidth: true
                placeholderText: "Apps, Dateien, Einstellungen suchen …"
                font.pixelSize: inhalt.gu * (inhalt.gross ? 1.1 : 0.85)
                onTextChanged: wurzel.runnerModel.query = text
                Keys.onDownPressed: ergebnisse.forceActiveFocus()
                Keys.onReturnPressed: ergebnisse.ersten()
                Keys.onEnterPressed: ergebnisse.ersten()
                Keys.onEscapePressed: wurzel.schliessen()
            }

            // ------------------------------------------------ Mitte: Suchergebnisse, alle Apps oder Startseite
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true

                // Suchergebnisse
                ListView {
                    id: ergebnisse
                    anchors.fill: parent
                    visible: suche.text !== ""
                    clip: true
                    model: wurzel.runnerModel.count ? wurzel.runnerModel.modelForRow(0) : null
                    spacing: 2
                    function ersten() {
                        if (model && count > 0) {
                            model.trigger(0, "", null);
                            wurzel.schliessen();
                        }
                    }
                    delegate: Zeile {
                        width: ListView.view.width
                        onAusgeloest: {
                            ergebnisse.model.trigger(index, "", null);
                            wurzel.schliessen();
                        }
                    }
                    Keys.onReturnPressed: if (currentIndex >= 0) { model.trigger(currentIndex, "", null); wurzel.schliessen(); }
                    Keys.onUpPressed: currentIndex <= 0 ? suche.forceActiveFocus() : decrementCurrentIndex()
                    PC3.Label {
                        anchors.centerIn: parent
                        visible: ergebnisse.count === 0
                        text: "Nichts gefunden. AUF BIBLIX GEHT DAS trotzdem."
                        opacity: 0.6
                    }
                }

                // Alle Apps
                ColumnLayout {
                    anchors.fill: parent
                    visible: suche.text === "" && inhalt.alleApps
                    spacing: inhalt.gu * 0.4
                    RowLayout {
                        PC3.ToolButton {
                            icon.name: "go-previous"
                            text: "Zurück"
                            onClicked: inhalt.alleApps = false
                        }
                        PC3.Label {
                            text: "Alle Apps"
                            font.weight: Font.Bold
                        }
                    }
                    GridView {
                        id: alleGitter
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        clip: true
                        cellWidth: Math.floor(width / inhalt.spalten)
                        cellHeight: cellWidth * 1.05
                        model: inhalt.alleApps ? wurzel.rootModel.modelForRow(1) : null
                        delegate: Kachel {
                            width: alleGitter.cellWidth
                            height: alleGitter.cellHeight
                            angeheftet: wurzel.rootModel.favoritesModel.isFavorite(model.favoriteId || "")
                            onAusgeloest: { alleGitter.model.trigger(index, "", null); wurzel.schliessen(); }
                            onAnheften: {
                                if (model.favoriteId) {
                                    if (angeheftet) wurzel.rootModel.favoritesModel.removeFavorite(model.favoriteId);
                                    else wurzel.rootModel.favoritesModel.addFavorite(model.favoriteId, -1);
                                }
                            }
                        }
                        QQC2.ScrollBar.vertical: PC3.ScrollBar {}
                    }
                }

                // Startseite
                ColumnLayout {
                    anchors.fill: parent
                    visible: suche.text === "" && !inhalt.alleApps
                    spacing: inhalt.gu * 0.6

                    // Schnellknöpfe
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: inhalt.gu * 0.4
                        Repeater {
                            model: [
                                { name: "S-Launcher", symbol: "s-launcher", id: "de.biblix.SLauncher", haupt: true },
                                { name: "Steam", symbol: "steam", id: "com.valvesoftware.Steam", haupt: false },
                                { name: "Dateien", symbol: "system-file-manager", id: "org.kde.dolphin", haupt: false },
                                { name: "Design", symbol: "de.biblix.Design", id: "de.biblix.Design", haupt: false }
                            ]
                            delegate: Rectangle {
                                required property var modelData
                                Layout.fillWidth: true
                                Layout.preferredHeight: inhalt.gu * (inhalt.gross ? 4.6 : 3.6)
                                radius: inhalt.gu * 0.6
                                color: schnellMaus.containsMouse ? inhalt.karteHover
                                     : (modelData.haupt ? Qt.rgba(inhalt.akzent.r, inhalt.akzent.g, inhalt.akzent.b, 0.16) : inhalt.karte)
                                scale: schnellMaus.pressed ? 0.95 : 1
                                Behavior on scale { NumberAnimation { duration: 120; easing.type: Easing.OutBack } }
                                Behavior on color { ColorAnimation { duration: 120 } }
                                ColumnLayout {
                                    anchors.centerIn: parent
                                    spacing: 2
                                    Kirigami.Icon {
                                        Layout.alignment: Qt.AlignHCenter
                                        implicitWidth: inhalt.gu * 1.8
                                        implicitHeight: inhalt.gu * 1.8
                                        source: modelData.symbol
                                    }
                                    PC3.Label {
                                        Layout.alignment: Qt.AlignHCenter
                                        text: modelData.name
                                        font.pixelSize: inhalt.gu * 0.65
                                    }
                                }
                                MouseArea {
                                    id: schnellMaus
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    onClicked: wurzel.starten(modelData.id)
                                }
                            }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        PC3.Label {
                            text: "Angeheftet"
                            opacity: 0.6
                            font.pixelSize: inhalt.gu * 0.7
                            Layout.fillWidth: true
                        }
                        PC3.ToolButton {
                            text: "Alle Apps"
                            icon.name: "go-next"
                            LayoutMirroring.enabled: true
                            font.pixelSize: inhalt.gu * 0.7
                            onClicked: inhalt.alleApps = true
                        }
                    }
                    PC3.Label {
                        visible: favGitter.count === 0
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        horizontalAlignment: Text.AlignHCenter
                        opacity: 0.55
                        font.pixelSize: inhalt.gu * 0.7
                        text: "Noch nichts angeheftet. Unter »Alle Apps« mit Rechtsklick anheften."
                    }
                    GridView {
                        id: favGitter
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        interactive: contentHeight > height
                        clip: true
                        cellWidth: Math.floor(width / inhalt.spalten)
                        cellHeight: cellWidth * 1.05
                        model: wurzel.rootModel.favoritesModel
                        delegate: Kachel {
                            width: favGitter.cellWidth
                            height: favGitter.cellHeight
                            angeheftet: true
                            onAusgeloest: { favGitter.model.trigger(index, "", null); wurzel.schliessen(); }
                            onAnheften: if (model.favoriteId) wurzel.rootModel.favoritesModel.removeFavorite(model.favoriteId)
                        }
                    }

                    PC3.Label {
                        text: "Zuletzt gespielt und benutzt"
                        opacity: 0.6
                        font.pixelSize: inhalt.gu * 0.7
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: inhalt.gu * 0.4
                        // Call of Duty über Windows (Spielstarter)
                        Karte {
                            Layout.fillWidth: true
                            titel: "Call of Duty"
                            untertitel: "startet über Windows"
                            symbol: "applications-games"
                            farbe: inhalt.akzent2
                            onAusgeloest: { wurzel.ausfuehren("biblix-windows-spiel cod"); wurzel.schliessen(); }
                        }
                        Repeater {
                            model: wurzel.zuletztModel
                            delegate: Karte {
                                required property int index
                                required property var model
                                visible: index < (inhalt.gross ? 3 : 2)
                                Layout.fillWidth: true
                                titel: model.display
                                untertitel: "zuletzt benutzt"
                                symbol: model.decoration
                                farbe: inhalt.akzent
                                onAusgeloest: { wurzel.zuletztModel.trigger(index, "", null); wurzel.schliessen(); }
                            }
                        }
                    }
                }
            }

            // ------------------------------------------------ Fuß: Spruch und Schrauben-Knöpfe
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: Qt.rgba(Kirigami.Theme.textColor.r, Kirigami.Theme.textColor.g, Kirigami.Theme.textColor.b, 0.12)
            }
            RowLayout {
                Layout.fillWidth: true
                spacing: inhalt.gu * 0.35
                PC3.Label {
                    Layout.fillWidth: true
                    text: inhalt.spruch
                    elide: Text.ElideRight
                    opacity: 0.7
                    font.family: "DejaVu Sans Mono"
                    font.pixelSize: inhalt.gu * 0.65
                    font.letterSpacing: 0.5
                    MouseArea {
                        anchors.fill: parent
                        onClicked: inhalt.neuerSpruch()
                    }
                }
                Schraube { symbol: "system-lock-screen"; tipp: "Sperren"; onAusgeloest: { wurzel.schliessen(); sitzung.lock(); } }
                Schraube { symbol: "system-suspend"; tipp: "Standby"; visible: sitzung.canSuspend; onAusgeloest: { wurzel.schliessen(); sitzung.suspend(); } }
                Schraube { symbol: "system-log-out"; tipp: "Abmelden"; onAusgeloest: { wurzel.schliessen(); wurzel.zeremonie("abmelden", () => sitzung.requestLogout()); } }
                Schraube { symbol: "biblix-windows-symbolic"; tipp: "Neustart in Windows"; onAusgeloest: { wurzel.schliessen(); wurzel.ausfuehren("biblix-neustart-windows"); } }
                Schraube { symbol: "system-reboot"; tipp: "Neustart"; onAusgeloest: { wurzel.schliessen(); sitzung.requestReboot(); } }
                Schraube { symbol: "system-shutdown"; tipp: "Ausschalten"; gefahr: true; onAusgeloest: { wurzel.schliessen(); wurzel.zeremonie("herunterfahren", () => sitzung.requestShutdown()); } }
            }
        }
    }

    // ---------------------------------------------------------------- Bausteine
    component Kachel: Item {
        id: kachel
        required property int index
        required property var model
        property bool angeheftet: false
        signal ausgeloest()
        signal anheften()

        Rectangle {
            anchors.fill: parent
            anchors.margins: inhalt.gu * 0.15
            radius: inhalt.gu * 0.5
            color: kachelMaus.containsMouse ? inhalt.karteHover : "transparent"
            Behavior on color { ColorAnimation { duration: 100 } }
        }
        ColumnLayout {
            anchors.centerIn: parent
            width: parent.width - inhalt.gu * 0.4
            spacing: 2
            Kirigami.Icon {
                Layout.alignment: Qt.AlignHCenter
                implicitWidth: inhalt.gu * (inhalt.gross ? 3 : 2.2)
                implicitHeight: implicitWidth
                source: kachel.model.decoration
                scale: kachelMaus.pressed ? 0.9 : (kachelMaus.containsMouse ? 1.08 : 1)
                Behavior on scale { NumberAnimation { duration: 140; easing.type: Easing.OutBack } }
            }
            PC3.Label {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: kachel.model.display
                elide: Text.ElideRight
                font.pixelSize: inhalt.gu * 0.65
            }
        }
        MouseArea {
            id: kachelMaus
            anchors.fill: parent
            hoverEnabled: true
            acceptedButtons: Qt.LeftButton | Qt.RightButton
            onClicked: maus => maus.button === Qt.RightButton ? kachel.anheften() : kachel.ausgeloest()
        }
        QQC2.ToolTip.text: (kachel.angeheftet ? "Rechtsklick: Lösen" : "Rechtsklick: Anheften")
        QQC2.ToolTip.visible: kachelMaus.containsMouse
        QQC2.ToolTip.delay: 1200
    }

    component Zeile: Rectangle {
        id: zeile
        required property int index
        required property var model
        signal ausgeloest()
        height: inhalt.gu * 2.3
        radius: inhalt.gu * 0.4
        color: (zeileMaus.containsMouse || ListView.isCurrentItem) ? inhalt.karteHover : "transparent"
        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: inhalt.gu * 0.5
            spacing: inhalt.gu * 0.5
            Kirigami.Icon {
                implicitWidth: inhalt.gu * 1.5
                implicitHeight: implicitWidth
                source: zeile.model.decoration
            }
            ColumnLayout {
                spacing: 0
                Layout.fillWidth: true
                PC3.Label { text: zeile.model.display; elide: Text.ElideRight; Layout.fillWidth: true }
                PC3.Label {
                    text: zeile.model.description || ""
                    visible: text !== ""
                    opacity: 0.6
                    font.pixelSize: inhalt.gu * 0.6
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
            }
        }
        MouseArea {
            id: zeileMaus
            anchors.fill: parent
            hoverEnabled: true
            onClicked: zeile.ausgeloest()
        }
    }

    component Karte: Rectangle {
        id: karte
        property string titel
        property string untertitel
        property var symbol
        property color farbe
        signal ausgeloest()
        implicitHeight: inhalt.gu * 2.8
        radius: inhalt.gu * 0.5
        color: karteMaus.containsMouse ? Qt.rgba(farbe.r, farbe.g, farbe.b, 0.28) : Qt.rgba(farbe.r, farbe.g, farbe.b, 0.12)
        Behavior on color { ColorAnimation { duration: 120 } }
        RowLayout {
            anchors.fill: parent
            anchors.margins: inhalt.gu * 0.4
            spacing: inhalt.gu * 0.4
            Kirigami.Icon {
                implicitWidth: inhalt.gu * 1.6
                implicitHeight: implicitWidth
                source: karte.symbol
            }
            ColumnLayout {
                spacing: 0
                Layout.fillWidth: true
                PC3.Label { text: karte.titel; elide: Text.ElideRight; Layout.fillWidth: true; font.pixelSize: inhalt.gu * 0.75 }
                PC3.Label { text: karte.untertitel; color: karte.farbe; font.pixelSize: inhalt.gu * 0.6; elide: Text.ElideRight; Layout.fillWidth: true }
            }
        }
        MouseArea {
            id: karteMaus
            anchors.fill: parent
            hoverEnabled: true
            onClicked: karte.ausgeloest()
        }
    }
}
