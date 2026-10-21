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

        Kirigami.Icon {
            id: symbol
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
