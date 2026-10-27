/*
    Biblix-Fensterleiste ("Typenschild"): jede App sitzt in derselben Fassung, das aktive Fenster hat
    eine LED, kleine Muttern zaehlen die offenen Fenster. Die Welt (Form und Farben) und der Lack
    (einfarbige Symbole) kommen aus Biblix Design. Fensterliste und Anheften wie bei KDE (TasksModel).
*/
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.extras as PlasmaExtras
import org.kde.taskmanager as TaskManager
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: leiste

    preferredRepresentation: fullRepresentation
    Plasmoid.constraintHints: Plasmoid.CanFillArea

    readonly property bool senkrecht: Plasmoid.formFactor === PlasmaCore.Types.Vertical
    readonly property var standard: ({
        grund: "#0f141c", flaeche: "#1a2029", karte: "#232a35", rand: "#313a48",
        text: "#e8ecf2", leise: "#8b95a5", akzent: "#378add", akzent2: "#ffd400"
    })
    readonly property var f: {
        let x = {};
        try { x = JSON.parse(Plasmoid.configuration.farben || "{}"); } catch (e) { x = {}; }
        return Object.assign({}, standard, x);
    }
    readonly property string welt: Plasmoid.configuration.welt || "typenschild"
    readonly property bool lack: Plasmoid.configuration.lack

    // Form und Farben je Welt. form: "kachel" (abgerundetes Quadrat) oder "rund".
    readonly property var stil: {
        const w = {
            typenschild: { form: "kachel", radius: 0.22, kachel: f.karte, rand: f.rand, randAktiv: f.akzent2, led: f.akzent2, metall: false },
            tower:       { form: "rund", radius: 0.5, kachel: "#15181c", rand: "#8b9098", randAktiv: "#9fd0ff", led: "#9fd0ff", metall: true },
            bank:        { form: "kachel", radius: 0.12, kachel: "#143528", rand: "#7d6213", randAktiv: "#e6c14a", led: "#e6c14a", metall: false },
            mac:         { form: "rund", radius: 0.5, kachel: "#fff4dc", rand: "#e3c98e", randAktiv: "#ffc72c", led: "#ffc72c", metall: false },
            delivery:    { form: "kachel", radius: 0.2, kachel: "#112b86", rand: "#2b50c8", randAktiv: "#ffd400", led: "#ffd400", metall: false },
            plexx:       { form: "kachel", radius: 0.16, kachel: "#1a1030", rand: "#3a2a55", randAktiv: "#ff8a3d", led: "#ff4d9d", metall: false },
            nass:        { form: "rund", radius: 0.5, kachel: "#e9fbfd", rand: "#22d3e6", randAktiv: "#ffb020", led: "#ffb020", metall: false }
        };
        return w[welt] || w.typenschild;
    }

    TaskManager.VirtualDesktopInfo { id: desktops }
    TaskManager.ActivityInfo { id: aktivitaeten }
    TaskManager.TasksModel {
        id: aufgaben
        groupMode: TaskManager.TasksModel.GroupApplications
        groupInline: false
        sortMode: TaskManager.TasksModel.SortManual
        separateLaunchers: false
        launchInPlace: true
        filterByScreen: Plasmoid.configuration.showOnlyCurrentScreen
        screenGeometry: Plasmoid.containment.screenGeometry
        filterByVirtualDesktop: true
        virtualDesktop: desktops.currentDesktop
        filterByActivity: true
        activity: aktivitaeten.currentActivity
        launcherList: Plasmoid.configuration.launchers
        onLauncherListChanged: Plasmoid.configuration.launchers = launcherList
    }

    function zeilenIndex(zeile, kind) {
        return kind === undefined ? aufgaben.makeModelIndex(zeile) : aufgaben.makeModelIndex(zeile, kind);
    }

    function klick(zeile, m) {
        const idx = zeilenIndex(zeile);
        if (m.IsLauncher || m.IsStartup) {
            aufgaben.requestActivate(idx);
            return;
        }
        if (m.IsGroupParent && m.ChildCount > 1) {
            // Fenster der Gruppe der Reihe nach nach vorn holen
            let aktiv = -1;
            for (let i = 0; i < m.ChildCount; i++) {
                if (aufgaben.data(zeilenIndex(zeile, i), TaskManager.AbstractTasksModel.IsActive)) aktiv = i;
            }
            aufgaben.requestActivate(zeilenIndex(zeile, (aktiv + 1) % m.ChildCount));
            return;
        }
        if (m.IsActive)
            aufgaben.requestToggleMinimized(idx);
        else
            aufgaben.requestActivate(idx);
    }

    function neuesFenster(zeile) {
        aufgaben.requestNewInstance(zeilenIndex(zeile));
    }

    function menueZeigen(element, zeile, info) {
        menue.zeile = zeile;
        menue.info = info;
        menue.visualParent = element;
        menue.openRelative();
    }

    function angeheftet(url) {
        return aufgaben.launcherPosition(url) >= 0;
    }

    PlasmaExtras.Menu {
        id: menue
        property int zeile: -1
        property var info: ({})
        PlasmaExtras.MenuItem {
            text: "Neues Fenster"
            icon: "window-new"
            visible: !!menue.info.url
            onClicked: aufgaben.requestNewInstance(leiste.zeilenIndex(menue.zeile))
        }
        PlasmaExtras.MenuItem {
            text: menue.info.angeheftet ? "Von der Leiste lösen" : "An die Leiste heften"
            icon: menue.info.angeheftet ? "window-unpin" : "window-pin"
            visible: !!menue.info.url
            onClicked: menue.info.angeheftet ? aufgaben.requestRemoveLauncher(menue.info.url)
                                             : aufgaben.requestAddLauncher(menue.info.url)
        }
        PlasmaExtras.MenuItem {
            text: menue.info.anzahl > 1 ? "Alle Fenster schließen" : "Schließen"
            icon: "window-close"
            visible: menue.info.anzahl > 0
            onClicked: aufgaben.requestClose(leiste.zeilenIndex(menue.zeile))
        }
    }

    fullRepresentation: Item {
        Layout.fillWidth: !leiste.senkrecht
        Layout.fillHeight: leiste.senkrecht
        Layout.minimumWidth: leiste.senkrecht ? 0 : liste.contentWidth
        Layout.preferredWidth: leiste.senkrecht ? -1 : liste.contentWidth

        ListView {
            id: liste
            anchors.fill: parent
            orientation: leiste.senkrecht ? ListView.Vertical : ListView.Horizontal
            interactive: false
            spacing: Math.round(Kirigami.Units.smallSpacing * 1.5)
            model: aufgaben
            delegate: Kachel {
                leisteRoot: leiste
                groesse: leiste.senkrecht ? liste.width : liste.height
            }
            add: Transition { NumberAnimation { property: "scale"; from: 0.4; to: 1; duration: 220; easing.type: Easing.OutBack } }
            displaced: Transition { NumberAnimation { properties: "x,y"; duration: 180; easing.type: Easing.OutCubic } }
        }
    }
}
