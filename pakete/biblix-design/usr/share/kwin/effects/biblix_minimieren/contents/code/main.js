/* Biblix Minimieren: Fenster blenden aus und schrumpfen leicht (statt in die Taskleiste zu fliegen). */
"use strict";

class BiblixMinimieren {
    constructor() {
        this.dauer = animationTime(220);
        effects.windowMinimized.connect(this.minimiert.bind(this));
        effects.windowUnminimized.connect(this.zurueck.bind(this));
    }

    minimiert(w) {
        if (effects.hasActiveFullScreenEffect || w.fullScreen) return;
        if (w.biblixZurueck) {
            cancel(w.biblixZurueck);
            delete w.biblixZurueck;
        }
        w.biblixWeg = animate({
            window: w,
            curve: QEasingCurve.InCubic,
            duration: this.dauer,
            animations: [
                { type: Effect.Scale, to: 0.9 },
                { type: Effect.Opacity, to: 0 }
            ]
        });
    }

    zurueck(w) {
        if (effects.hasActiveFullScreenEffect || w.fullScreen) return;
        if (w.biblixWeg) {
            cancel(w.biblixWeg);
            delete w.biblixWeg;
        }
        w.biblixZurueck = animate({
            window: w,
            curve: QEasingCurve.OutBack,
            duration: this.dauer,
            animations: [
                { type: Effect.Scale, from: 0.9 },
                { type: Effect.Opacity, from: 0 }
            ]
        });
    }
}

new BiblixMinimieren();
