// Sternenflug: Sterne fliegen aus der Mitte auf dich zu
import QtQuick
import QtQuick.Particles

Szene {
    id: s

    ParticleSystem { id: sys; anchors.fill: parent; paused: !s.laeuft }
    ImageParticle {
        system: sys; groups: ["weiss"]
        source: "qrc:///particleresources/glowdot.png"
        color: s.c("text"); colorVariation: 0.05; alpha: 0.9
        entryEffect: ImageParticle.Fade
    }
    ImageParticle {
        system: sys; groups: ["farbe"]
        source: "qrc:///particleresources/glowdot.png"
        color: s.c("akzent"); alpha: 0.9
        entryEffect: ImageParticle.Fade
    }
    Emitter {
        system: sys; group: "weiss"
        x: parent.width / 2 - 260; y: parent.height / 2 - 160; width: 520; height: 320
        emitRate: 220 * s.tempo; lifeSpan: 4500; startTime: 4500; lifeSpanVariation: 800
        size: 4; endSize: 26; sizeVariation: 3
        velocity: AngleDirection { angleVariation: 180; magnitude: 30 * s.tempo; magnitudeVariation: 20 }
    }
    Emitter {
        system: sys; group: "farbe"
        x: parent.width / 2 - 60; y: parent.height / 2 - 40; width: 120; height: 80
        emitRate: 40 * s.tempo; lifeSpan: 5000; startTime: 5000
        size: 6; endSize: 34
        velocity: AngleDirection { angleVariation: 180; magnitude: 30 * s.tempo; magnitudeVariation: 20 }
    }
    // Abstossung aus der Mitte: je weiter weg, desto schneller (Warp-Effekt)
    Attractor {
        system: sys; anchors.fill: parent
        pointX: width / 2; pointY: height / 2
        strength: -45 * s.tempo
        affectedParameter: Attractor.Acceleration
        proportionalToDistance: Attractor.Constant
    }
}
