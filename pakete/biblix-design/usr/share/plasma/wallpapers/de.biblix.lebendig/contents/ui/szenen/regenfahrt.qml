// Kamerafahrt um den Exabibi Tower bei Nacht und Regen (Bibi Tech).
// In Blender gerendertes Video (kunst/blender/exatower_regenfahrt.py), laeuft als nahtlose Schleife.
// Pausiert wie alle Szenen bei Spielen und maximierten Fenstern; ohne Ton.
import QtQuick
import QtMultimedia

Szene {
    id: s

    readonly property url video: Qt.resolvedUrl("../../videos/exatower-regen.mp4")

    Rectangle {
        anchors.fill: parent
        color: "#03060f"
    }
    MediaPlayer {
        id: spieler
        source: s.video
        loops: MediaPlayer.Infinite
        videoOutput: ausgabe
        playbackRate: Math.max(0.5, Math.min(1.5, s.tempo))
        onMediaStatusChanged: if (mediaStatus === MediaPlayer.LoadedMedia && s.laeuft) play()
    }
    VideoOutput {
        id: ausgabe
        anchors.fill: parent
        fillMode: VideoOutput.PreserveAspectCrop
    }
    // Standbild, bis das erste Videobild da ist (kein schwarzes Aufblitzen)
    Image {
        anchors.fill: parent
        source: Qt.resolvedUrl("../../videos/exatower-regen.jpg")
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        opacity: spieler.playbackState === MediaPlayer.PlayingState && spieler.position > 200 ? 0 : 1
        Behavior on opacity { NumberAnimation { duration: 600 } }
    }
    onLaeuftChanged: laeuft ? spieler.play() : spieler.pause()
    Component.onCompleted: if (laeuft) spieler.play()
}
