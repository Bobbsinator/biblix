/*
    Biblix lebendig: animierte Hintergruende in den Farben von Biblix Design.
    Jede Szene liegt in szenen/<name>.qml und erbt von Szene.qml (Farben f, laeuft, tempo, sprueche).
    Pausiert, solange auf diesem Bildschirm ein Fenster maximiert oder im Vollbild ist (Spiele!).
*/
import QtQuick
import org.kde.plasma.plasmoid
import org.kde.taskmanager as TaskManager

WallpaperItem {
    id: root

    readonly property var standard: ({
        grund: "#0f141c", flaeche: "#1a2029", karte: "#232a35", rand: "#313a48",
        text: "#e8ecf2", leise: "#8b95a5", akzent: "#378add", akzent2: "#ffd400"
    })
    readonly property var farben: {
        let f = {};
        try { f = JSON.parse(root.configuration.Farben || "{}"); } catch (e) { f = {}; }
        return Object.assign({}, standard, f);
    }
    readonly property var sprueche: (root.configuration.Sprueche || "").split("\n").filter(z => z.trim().length > 0)
    property int abdecker: 0
    readonly property bool laeuft: !(root.configuration.Pausieren && abdecker > 0)

    Rectangle {
        anchors.fill: parent
        color: root.farben.grund
    }

    Loader {
        id: szene
        anchors.fill: parent
        asynchronous: true
        source: Qt.resolvedUrl("szenen/" + (root.configuration.Szene || "sternenflug") + ".qml")
        onStatusChanged: if (status === Loader.Error) source = Qt.resolvedUrl("szenen/sternenflug.qml")
    }
    Binding { target: szene.item; property: "f"; value: root.farben; when: szene.status === Loader.Ready }
    Binding { target: szene.item; property: "laeuft"; value: root.laeuft; when: szene.status === Loader.Ready }
    Binding { target: szene.item; property: "tempo"; value: Math.max(0.2, root.configuration.Tempo || 1.0); when: szene.status === Loader.Ready }
    Binding { target: szene.item; property: "sprueche"; value: root.sprueche; when: szene.status === Loader.Ready }

    // ---- Pause bei maximierten Fenstern und Vollbild (nur dieser Bildschirm, aktuelle Arbeitsflaeche)
    TaskManager.VirtualDesktopInfo { id: desktops }
    TaskManager.ActivityInfo { id: aktivitaeten }
    TaskManager.TasksModel {
        id: aufgaben
        filterByScreen: true
        filterByVirtualDesktop: true
        filterByActivity: true
        // filterMinimized zusammen mit den anderen Filtern liefert in Plasma 6.3 gar nichts: selbst pruefen
        screenGeometry: root.parent && root.parent.screenGeometry ? root.parent.screenGeometry : Qt.rect(0, 0, 0, 0)
        virtualDesktop: desktops.currentDesktop
        activity: aktivitaeten.currentActivity
    }
    // Jedes Fenster einzeln beobachten: maximiert oder Vollbild?
    Instantiator {
        id: fensterListe
        model: aufgaben
        delegate: QtObject {
            required property var model
            readonly property bool deckt: model.IsMinimized !== true && (model.IsMaximized === true || model.IsFullScreen === true)
            onDecktChanged: zaehlen.restart()
            Component.onCompleted: zaehlen.restart()
            Component.onDestruction: zaehlen.restart()
        }
    }
    Timer {
        id: zaehlen
        interval: 200
        onTriggered: {
            let n = 0;
            for (let i = 0; i < fensterListe.count; i++) {
                const o = fensterListe.objectAt(i);
                if (o && o.deckt)
                    n++;
            }
            root.abdecker = n;
        }
    }
    Component.onCompleted: zaehlen.restart()
}
