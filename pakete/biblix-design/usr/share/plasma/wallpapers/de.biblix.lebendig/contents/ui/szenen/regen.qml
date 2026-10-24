// Regen: schräge Regenfäden, unten spritzen Tropfen
import QtQuick
import QtQuick.Particles

Szene {
    id: s

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.0; color: s.mix("grund", "rand", 0.5) }
            GradientStop { position: 1.0; color: s.c("grund") }
        }
    }
    ParticleSystem { id: sys; anchors.fill: parent; paused: !s.laeuft }
    ItemParticle {
        system: sys; groups: ["faden"]
        delegate: Rectangle {
            width: 1.6; height: 26; radius: 1
            rotation: 12
            color: s.c("akzent", 0.55)
        }
    }
    ImageParticle {
        system: sys; groups: ["spritzer"]
        source: "qrc:///particleresources/glowdot.png"
        color: s.c("akzent"); alpha: 0.6
    }
    Emitter {
        system: sys; group: "faden"
        x: -parent.width * 0.2; y: -40; width: parent.width * 1.2; height: 1
        emitRate: 160 * s.tempo; lifeSpan: 1700; startTime: 1700
        velocity: PointDirection { x: 160; y: 900 * s.tempo; yVariation: 120 }
    }
    // Aufprall unten: kleine Spritzer
    Emitter {
        system: sys; group: "spritzer"
        x: 0; y: parent.height - 4; width: parent.width; height: 2
        emitRate: 60 * s.tempo; lifeSpan: 450; startTime: 450
        size: 6; endSize: 0
        velocity: AngleDirection { angle: 270; angleVariation: 50; magnitude: 80; magnitudeVariation: 40 }
        acceleration: PointDirection { y: 300 }
    }
}
