// Schnee: leiser Flockenfall in drei Tiefen
import QtQuick
import QtQuick.Particles

Szene {
    id: s

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.mix("grund", "akzent", 0.12) }
            GradientStop { position: 1.0; color: s.c("grund") }
        }
    }
    ParticleSystem { id: sys; anchors.fill: parent; paused: !s.laeuft }
    ImageParticle {
        system: sys
        source: "qrc:///particleresources/fuzzydot.png"
        color: s.c("text"); alpha: 0.85; colorVariation: 0.05
    }
    // hinten: klein und langsam
    Emitter {
        system: sys; x: -50; y: -20; width: parent.width + 100; height: 1
        emitRate: 30 * s.tempo; lifeSpan: 22000; startTime: 22000
        size: 5; sizeVariation: 2
        velocity: PointDirection { y: 45 * s.tempo; yVariation: 10; xVariation: 8 }
    }
    // vorne: gross und schneller
    Emitter {
        system: sys; x: -50; y: -40; width: parent.width + 100; height: 1
        emitRate: 9 * s.tempo; lifeSpan: 12000; startTime: 12000
        size: 14; sizeVariation: 6
        velocity: PointDirection { y: 95 * s.tempo; yVariation: 20; xVariation: 15 }
    }
    // Beim Start einmal Flocken ueber das ganze Bild streuen (sonst faengt es oben leer an)
    Emitter {
        id: saat
        system: sys; anchors.fill: parent; emitRate: 0; lifeSpan: 16000
        size: 7; sizeVariation: 5
        velocity: PointDirection { y: 60 * s.tempo; yVariation: 25; xVariation: 10 }
    }
    Timer { interval: 300; running: true; onTriggered: saat.burst(Math.round(s.width * s.height / 4500)) }
    Wander { system: sys; anchors.fill: parent; xVariance: 60; pace: 30 }
    // Schneedecke unten
    Rectangle {
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: parent.height * 0.06
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.c("text", 0.0) }
            GradientStop { position: 1.0; color: s.c("text", 0.18) }
        }
    }
}
