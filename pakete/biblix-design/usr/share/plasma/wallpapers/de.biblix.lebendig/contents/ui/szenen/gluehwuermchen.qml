// Glühwürmchen: warme Lichtpunkte schweben, leuchten auf und verglimmen
import QtQuick
import QtQuick.Particles

Szene {
    id: s

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.c("grund") }
            GradientStop { position: 1.0; color: s.mix("grund", "flaeche", 0.8) }
        }
    }
    ParticleSystem { id: sys; anchors.fill: parent; paused: !s.laeuft }
    ImageParticle {
        system: sys; groups: ["warm"]
        source: "qrc:///particleresources/glowdot.png"
        color: s.c("akzent2"); colorVariation: 0.08; alpha: 0.95
        entryEffect: ImageParticle.Fade
    }
    ImageParticle {
        system: sys; groups: ["kalt"]
        source: "qrc:///particleresources/glowdot.png"
        color: s.c("akzent"); alpha: 0.8
        entryEffect: ImageParticle.Fade
    }
    Emitter {
        system: sys; group: "warm"; anchors.fill: parent
        emitRate: 14 * s.tempo; lifeSpan: 9000; startTime: 9000; lifeSpanVariation: 3000
        size: 34; sizeVariation: 14; endSize: 8
        velocity: PointDirection { xVariation: 12; yVariation: 12 }
    }
    Emitter {
        system: sys; group: "kalt"; anchors.fill: parent
        emitRate: 3 * s.tempo; lifeSpan: 8000; startTime: 8000; lifeSpanVariation: 2000
        size: 26; sizeVariation: 8; endSize: 6
        velocity: PointDirection { xVariation: 10; yVariation: 10 }
    }
    Wander { system: sys; anchors.fill: parent; xVariance: 40; yVariance: 40; pace: 40 * s.tempo }
}
