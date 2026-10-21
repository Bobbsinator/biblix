/*
    Biblix Fenster-Animationen (KWin-Effekt)
    Oeffnen:   bibi-pop | hochgleiten | aufbauen | einblenden | aus
    Schliessen: zusammenziehen | wegfallen | abbauen | ausblenden | aus
    Einstellungen: kwinrc [Effect-biblix_fenster] Oeffnen=, Schliessen=  (setzt die App "Biblix Design")
    Aufbau nach dem KWin-Effekt "scale" (GPL-2.0-or-later).
*/
"use strict";

const ausgenommen = [
    "ksmserver ksmserver",
    "ksmserver-logout-greeter ksmserver-logout-greeter",
    "ksplashqml ksplashqml",
    "spectacle spectacle",
    "spectacle org.kde.spectacle",
];

class BiblixFenster {
    constructor() {
        effect.configChanged.connect(this.laden.bind(this));
        effect.animationEnded.connect(this.aufraeumen.bind(this));
        effects.windowAdded.connect(this.geoeffnet.bind(this));
        effects.windowClosed.connect(this.geschlossen.bind(this));
        effects.windowDataChanged.connect(this.datenGeaendert.bind(this));
        this.laden();
    }

    laden() {
        this.oeffnen = effect.readConfig("Oeffnen", "bibi-pop");
        this.schliessen = effect.readConfig("Schliessen", "zusammenziehen");
        this.dauer = animationTime(260);
    }

    static passend(w) {
        if (w.windowClass == "plasmashell plasmashell" || w.windowClass == "plasmashell org.kde.plasmashell") {
            return w.hasDecoration;
        }
        if (ausgenommen.indexOf(w.windowClass) != -1) return false;
        // Spiele und Vollbild nie animieren
        if (w.fullScreen) return false;
        if (w.hasDecoration) return true;
        if (w.popupWindow || w.lockScreen || w.outline || !w.managed) return false;
        return w.normalWindow || w.dialog;
    }

    rollenAn(w) {
        w.setData(Effect.WindowForceBackgroundContrastRole, true);
        w.setData(Effect.WindowForceBlurRole, true);
    }

    aufraeumen(w) {
        w.setData(Effect.WindowForceBackgroundContrastRole, null);
        w.setData(Effect.WindowForceBlurRole, null);
    }

    geoeffnet(w) {
        if (this.oeffnen == "aus" || effects.hasActiveFullScreenEffect) return;
        if (!BiblixFenster.passend(w) || !w.visible) return;
        if (effect.isGrabbed(w, Effect.WindowAddedGrabRole)) return;
        let a;
        if (this.oeffnen == "bibi-pop") {
            // waechst aus der Mitte und federt leicht nach
            a = { curve: QEasingCurve.OutBack, duration: this.dauer, animations: [
                { type: Effect.Scale, from: 0.72 },
                { type: Effect.Opacity, from: 0, curve: QEasingCurve.OutCubic } ] };
        } else if (this.oeffnen == "hochgleiten") {
            a = { curve: QEasingCurve.OutCubic, duration: this.dauer, animations: [
                { type: Effect.Translation, from: { value1: 0, value2: 70 } },
                { type: Effect.Opacity, from: 0 } ] };
        } else if (this.oeffnen == "aufbauen") {
            a = { curve: QEasingCurve.OutQuart, duration: this.dauer + 60, animations: [
                { type: Effect.Scale, from: { value1: 1.0, value2: 0.05 } },
                { type: Effect.Opacity, from: 0.2 } ] };
        } else {
            a = { curve: QEasingCurve.OutCubic, duration: this.dauer, animations: [
                { type: Effect.Opacity, from: 0 } ] };
        }
        this.rollenAn(w);
        a.window = w;
        w.biblixRein = animate(a);
    }

    geschlossen(w) {
        if (this.schliessen == "aus" || effects.hasActiveFullScreenEffect) return;
        if (!BiblixFenster.passend(w) || !w.visible || w.skipsCloseAnimation) return;
        if (effect.isGrabbed(w, Effect.WindowClosedGrabRole)) return;
        if (w.biblixRein) {
            cancel(w.biblixRein);
            delete w.biblixRein;
        }
        let a;
        const d = Math.round(this.dauer * 0.8);
        if (this.schliessen == "zusammenziehen") {
            a = { curve: QEasingCurve.InBack, duration: d, animations: [
                { type: Effect.Scale, to: 0.7 },
                { type: Effect.Opacity, to: 0, curve: QEasingCurve.InCubic } ] };
        } else if (this.schliessen == "wegfallen") {
            a = { curve: QEasingCurve.InQuad, duration: d + 80, animations: [
                { type: Effect.Translation, to: { value1: 0, value2: 160 } },
                { type: Effect.Scale, to: 0.94 },
                { type: Effect.Opacity, to: 0 } ] };
        } else if (this.schliessen == "abbauen") {
            a = { curve: QEasingCurve.InQuart, duration: d + 60, animations: [
                { type: Effect.Scale, to: { value1: 1.0, value2: 0.05 } },
                { type: Effect.Opacity, to: 0 } ] };
        } else {
            a = { curve: QEasingCurve.InCubic, duration: d, animations: [
                { type: Effect.Opacity, to: 0 } ] };
        }
        this.rollenAn(w);
        a.window = w;
        w.biblixRaus = animate(a);
    }

    datenGeaendert(w, rolle) {
        if (rolle == Effect.WindowAddedGrabRole && w.biblixRein && effect.isGrabbed(w, rolle)) {
            cancel(w.biblixRein);
            delete w.biblixRein;
            this.aufraeumen(w);
        } else if (rolle == Effect.WindowClosedGrabRole && w.biblixRaus && effect.isGrabbed(w, rolle)) {
            cancel(w.biblixRaus);
            delete w.biblixRaus;
            this.aufraeumen(w);
        }
    }
}

new BiblixFenster();
