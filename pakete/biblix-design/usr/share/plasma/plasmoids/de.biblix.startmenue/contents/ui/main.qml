/*
    Bibi-Startmenü (Biblix Design)
    Modelle nach dem Vorbild von Kickoff (KDE, GPL-2.0-or-later).
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.private.kicker as Kicker
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: menue

    readonly property bool vollbild: Plasmoid.configuration.stil === "vollbild"
    property var sprueche: ["AUF BIBLIX GEHT DAS."]
    property string designName: ""

    // ---------------------------------------------------------------- Modelle
    readonly property Kicker.RootModel rootModel: Kicker.RootModel {
        autoPopulate: false
        appletInterface: menue
        appNameFormat: 0
        flat: true
        sorted: true
        showSeparators: false
        showTopLevelItems: true
        showAllApps: true
        showAllAppsCategorized: false
        showRecentApps: false
        showRecentDocs: false
        showPowerSession: false
        showFavoritesPlaceholder: true
        Component.onCompleted: {
            favoritesModel.initForClient("de.biblix.startmenue.favorites.instance-" + Plasmoid.id);
            if (!Plasmoid.configuration.favoritesPortedToKAstats) {
                if (favoritesModel.count < 1) {
                    favoritesModel.portOldFavorites(Plasmoid.configuration.favorites);
                }
                Plasmoid.configuration.favoritesPortedToKAstats = true;
            }
            refresh();
        }
    }

    readonly property Kicker.RunnerModel runnerModel: Kicker.RunnerModel {
        appletInterface: menue
        mergeResults: true
        favoritesModel: menue.rootModel.favoritesModel
    }

    readonly property Kicker.RecentUsageModel zuletztModel: Kicker.RecentUsageModel {
        favoritesModel: menue.rootModel.favoritesModel
        ordering: 0
        shownItems: Kicker.RecentUsageModel.OnlyApps
    }

    // Befehle ausführen und Dateien lesen
    P5Support.DataSource {
        id: befehle
        engine: "executable"
        connectedSources: []
        onNewData: (quelle, daten) => {
            const aus = (daten["stdout"] || "").trim();
            if (quelle.indexOf("sprueche.txt") >= 0) {
                const liste = aus.split("\n").filter(z => z.trim() !== "" && !z.startsWith("#"));
                if (liste.length > 0) {
                    menue.sprueche = liste;
                }
            } else if (quelle.indexOf("palette.json") >= 0) {
                try { menue.designName = JSON.parse(aus).name || ""; } catch (e) {}
            }
            disconnectSource(quelle);
        }
    }

    function ausfuehren(befehl) {
        befehle.connectSource(befehl);
    }

    function starten(desktopId) {
        ausfuehren("kstart --application " + desktopId);
        menue.schliessen();
    }

    function schliessen() {
        if (vollbild) {
            dashboard.visible = false;
        } else {
            menue.expanded = false;
        }
    }

    // Sprüche und Designname neu einlesen (beim Öffnen; nach Updates oder Designwechsel)
    function aktualisieren() {
        ausfuehren("cat /usr/share/biblix/design/sprueche.txt");
        ausfuehren("sh -c 'cat \"$HOME/.config/biblix/palette.json\"'");
    }

    Component.onCompleted: {
        aktualisieren();
        if (Plasmoid.hasOwnProperty("activationTogglesExpanded")) {
            Plasmoid.activationTogglesExpanded = !vollbild;
        }
    }

    // ---------------------------------------------------------------- Darstellung
    Plasmoid.icon: Plasmoid.configuration.icon
    preferredRepresentation: compactRepresentation
    switchWidth: Kirigami.Units.gridUnit * 10
    switchHeight: Kirigami.Units.gridUnit * 10

    compactRepresentation: MouseArea {
        id: knopf
        hoverEnabled: true
        Layout.minimumWidth: Kirigami.Units.iconSizes.medium
        Layout.preferredWidth: height
        property bool warOffen

        onPressed: warOffen = menue.vollbild ? dashboard.visible : menue.expanded
        onClicked: {
            if (menue.vollbild) {
                dashboard.toggle();
            } else {
                menue.expanded = !warOffen;
            }
        }

        // Gelber B-Knopf wie an Bibi Phone und Bibi Pad (Taskleiste "Typenschild")
        Item {
            id: bk
            visible: Plasmoid.configuration.knopf === "bknopf"
            anchors.centerIn: parent
            width: Math.min(parent.width, parent.height) * 0.8
            height: width
            scale: knopf.pressed ? 0.9 : (knopf.containsMouse ? 1.06 : 1.0)
            Behavior on scale { NumberAnimation { duration: Kirigami.Units.shortDuration; easing.type: Easing.OutBack } }
            readonly property color farbe: Plasmoid.configuration.knopfFarbe || "#ffd400"
            Rectangle {
                anchors.centerIn: parent
                width: parent.width * 1.18
                height: width
                radius: width / 2
                opacity: knopf.containsMouse ? 0.45 : 0.25
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "transparent" }
                    GradientStop { position: 0.5; color: Qt.alpha(bk.farbe, 0.6) }
                    GradientStop { position: 1.0; color: "transparent" }
                }
            }
            Rectangle {
                anchors.fill: parent
                radius: width / 2
                border.width: Math.max(1, width * 0.05)
                border.color: Qt.darker(bk.farbe, 2.2)
                gradient: Gradient {
                    GradientStop { position: 0.0; color: Qt.lighter(bk.farbe, 1.25) }
                    GradientStop { position: 1.0; color: Qt.darker(bk.farbe, 1.2) }
                }
                Rectangle {
                    anchors.fill: parent
                    anchors.margins: parent.width * 0.12
                    radius: width / 2
                    color: "transparent"
                    border.width: 1
                    border.color: Qt.rgba(0, 0, 0, 0.14)
                }
                Text {
                    anchors.centerIn: parent
                    anchors.horizontalCenterOffset: 1
                    text: "B"
                    color: Qt.darker(bk.farbe, 3.5)
                    font.family: "DejaVu Sans"
                    font.bold: true
                    font.pixelSize: parent.height * 0.6
                }
            }
        }
        Kirigami.Icon {
            id: symbol
            visible: Plasmoid.configuration.knopf !== "bknopf"
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing / 2
            source: Plasmoid.icon
            active: knopf.containsMouse
            scale: knopf.pressed ? 0.88 : (knopf.containsMouse ? 1.06 : 1.0)
            Behavior on scale { NumberAnimation { duration: Kirigami.Units.shortDuration; easing.type: Easing.OutBack } }
        }
    }

    fullRepresentation: Inhalt {
        wurzel: menue
        gross: false
    }

    Kicker.DashboardWindow {
        id: dashboard
        visualParent: menue.compactRepresentationItem
        backgroundColor: Qt.rgba(Kirigami.Theme.backgroundColor.r, Kirigami.Theme.backgroundColor.g,
                                 Kirigami.Theme.backgroundColor.b, 0.92)
        onKeyEscapePressed: dashboard.visible = false
        mainItem: Item {
            anchors.fill: parent
            Inhalt {
                anchors.centerIn: parent
                width: Math.min(parent.width - Kirigami.Units.gridUnit * 4, Kirigami.Units.gridUnit * 60)
                height: Math.min(parent.height - Kirigami.Units.gridUnit * 4, Kirigami.Units.gridUnit * 42)
                wurzel: menue
                gross: true
                offen: dashboard.visible
            }
            MouseArea {
                anchors.fill: parent
                z: -1
                onClicked: dashboard.visible = false
            }
        }
    }

    Plasmoid.contextualActions: [
        PlasmaCore.Action {
            text: "Biblix Design öffnen…"
            icon.name: "de.biblix.Design"
            onTriggered: menue.ausfuehren("kstart --application de.biblix.Design")
        }
    ]
}
