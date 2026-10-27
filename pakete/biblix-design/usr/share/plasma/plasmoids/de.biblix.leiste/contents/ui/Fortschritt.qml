// Fortschritt einer App (z. B. Download), ueber die Smart-Launcher-Schnittstelle der KDE-Fensterleiste.
// Eigene Datei, damit die Leiste ohne dieses private Modul trotzdem laeuft (Loader schlaegt dann nur fehl).
import QtQuick
import org.kde.plasma.private.taskmanager as TaskManagerApplet

TaskManagerApplet.SmartLauncherItem {
    readonly property bool sichtbar: progressVisible
    readonly property real wert: progress / 100
}
