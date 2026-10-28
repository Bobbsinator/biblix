/*
    Biblix-Fensterleiste in vier Formen (setzt Biblix Design):
    zonen:       schlichte Symbole, Trennlinie zum Startknopf, Strich unter offenen Fenstern (Standard)
    inseln:      dieselben Symbole auf einer eigenen schwebenden Insel in der Mitte
    kopfzeile:   Symbole links, in der Mitte Name und Titel des aktiven Fensters
    typenschild: jede App in einer Fassung, LED fuers aktive Fenster, Muttern zaehlen die Fenster;
                 nur hier wechselt die Welt (Form und Farben) mit dem Preset.
    Lack (einfarbige Symbole) gilt fuer alle Formen. Fensterliste und Anheften wie bei KDE (TasksModel).
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
    readonly property string form: Plasmoid.configuration.form || "zonen"
    readonly property bool flach: form !== "typenschild"
    readonly property string welt: flach ? "typenschild" : (Plasmoid.configuration.welt || "typenschild")
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

    // Kopfzeile: Name und Titel des aktiven Fensters (neu lesen, wenn sich etwas aendert)
    property int stand: 0
    Connections {
        target: aufgaben
        function onDataChanged() { leiste.stand++; }
        function onActiveTaskChanged() { leiste.stand++; }
        function onCountChanged() { leiste.stand++; }
    }
    readonly property var aktivesFenster: {
        leiste.stand;
        if (form !== "kopfzeile") return null;
        const R = TaskManager.AbstractTasksModel;
        for (let z = 0; z < aufgaben.count; z++) {
            const idx = zeilenIndex(z);
            if (!aufgaben.data(idx, R.IsActive)) continue;
            let titel = aufgaben.data(idx, 0) || "";
            const kinder = aufgaben.data(idx, R.ChildCount) || 0;
            for (let i = 0; i < kinder; i++) {
                const k = zeilenIndex(z, i);
                if (aufgaben.data(k, R.IsActive)) titel = aufgaben.data(k, 0) || titel;
            }
            return { app: aufgaben.data(idx, R.AppName) || "", titel: titel };
        }
        return null;
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
        id: flaeche
        // Abstand links (Trennlinie) und Innenrand der Insel
        readonly property real rand: leiste.flach ? Kirigami.Units.smallSpacing * 2 : 0
        readonly property real insel: leiste.form === "inseln" ? Kirigami.Units.smallSpacing * 2 : 0
        Layout.fillWidth: !leiste.senkrecht
        Layout.fillHeight: leiste.senkrecht
        Layout.minimumWidth: leiste.senkrecht ? 0 : liste.contentWidth + 2 * (rand + insel)
        Layout.preferredWidth: leiste.senkrecht ? -1 : Layout.minimumWidth

        // Drei Zonen und Kopfzeile: feine Linie zwischen Startknopf und Fenstern
        Rectangle {
            visible: !leiste.senkrecht && (leiste.form === "zonen" || leiste.form === "kopfzeile")
            x: 0
            width: 1
            height: Math.round(parent.height * 0.55)
            anchors.verticalCenter: parent.verticalCenter
            color: leiste.f.rand
        }
        // Inseln: die Fenster schweben auf einer eigenen Insel
        Rectangle {
            visible: leiste.form === "inseln" && !leiste.senkrecht && liste.count > 0
            x: liste.x - flaeche.insel
            width: liste.width + 2 * flaeche.insel
            height: parent.height
            radius: Math.round(height * 0.3)
            color: Qt.alpha(leiste.f.grund, 0.94)
            border.width: 1
            border.color: Qt.alpha(leiste.f.rand, 0.8)
        }
        // Kopfzeile: Name und Titel des aktiven Fensters
        Column {
            id: kopf
            visible: leiste.form === "kopfzeile" && !leiste.senkrecht && leiste.aktivesFenster !== null
            readonly property real links: liste.x + liste.width + flaeche.rand * 3
            width: Math.min(Math.max(appName.implicitWidth, fensterTitel.implicitWidth), Math.max(0, parent.width - links - flaeche.rand))
            x: Math.max(links, (parent.width - width) / 2)
            anchors.verticalCenter: parent.verticalCenter
            spacing: 0
            Text {
                id: appName
                width: Math.min(implicitWidth, kopf.width)
                text: leiste.aktivesFenster ? leiste.aktivesFenster.app : ""
                color: leiste.f.text
                elide: Text.ElideRight
                font.pixelSize: Math.round(flaeche.height * 0.32)
                font.weight: Font.DemiBold
            }
            Text {
                id: fensterTitel
                width: Math.min(implicitWidth, kopf.width)
                text: {
                    const a = leiste.aktivesFenster;
                    if (!a) return "";
                    // Titel ohne angehaengten App-Namen ("Seite — Mozilla Firefox" -> "Seite"):
                    // letzter Abschnitt faellt weg, wenn er ein Wort mit dem App-Namen teilt
                    const teile = a.titel.split(/\s+[–—-]\s+/);
                    if (teile.length < 2) return a.titel;
                    const woerter = a.app.toLowerCase().split(/\s+/).filter(w => w.length > 2);
                    const letzter = teile[teile.length - 1].toLowerCase();
                    return woerter.some(w => letzter.indexOf(w) >= 0) ? a.titel.slice(0, a.titel.lastIndexOf(teile[teile.length - 1])).replace(/\s+[–—-]\s+$/, "") : a.titel;
                }
                color: leiste.f.leise
                elide: Text.ElideRight
                font.pixelSize: Math.round(flaeche.height * 0.22)
            }
        }

        ListView {
            id: liste
            x: leiste.senkrecht ? 0 : (leiste.form === "inseln" ? Math.round((parent.width - width) / 2) : flaeche.rand + flaeche.insel)
            width: leiste.senkrecht ? parent.width : contentWidth
            height: parent.height
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
