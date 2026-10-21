/* Biblix Spielmodus: leuchtet in der Akzentfarbe, solange GameMode aktiv ist. */
import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: wurzel
    property bool aktiv: false
    preferredRepresentation: compactRepresentation
    toolTipMainText: "Spielmodus"
    toolTipSubText: aktiv ? "GameMode ist aktiv: volle Leistung für dein Spiel." : "Kein Spiel mit GameMode aktiv."
    Plasmoid.status: aktiv ? PlasmaCore.Types.ActiveStatus : PlasmaCore.Types.PassiveStatus

    P5Support.DataSource {
        engine: "executable"
        connectedSources: ["gamemoded -s"]
        interval: 3000
        onNewData: (quelle, daten) => { wurzel.aktiv = (daten["stdout"] || "").indexOf("is active") >= 0; }
    }

    compactRepresentation: Item {
        Layout.preferredWidth: height
        Kirigami.Icon {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            source: "input-gaming-symbolic"
            isMask: true
            color: wurzel.aktiv ? Kirigami.Theme.highlightColor : Kirigami.Theme.textColor
            opacity: wurzel.aktiv ? 1 : 0.35
            SequentialAnimation on scale {
                running: wurzel.aktiv
                loops: Animation.Infinite
                NumberAnimation { to: 1.08; duration: 900; easing.type: Easing.InOutSine }
                NumberAnimation { to: 1.0; duration: 900; easing.type: Easing.InOutSine }
            }
        }
    }
}
