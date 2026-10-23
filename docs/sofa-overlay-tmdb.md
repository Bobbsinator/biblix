# Sofa-Modus, Leistungs-Overlay und TMDB-Poster (24.10.2026)

Wunsch E, F, G aus der Ideenliste. Dazu Fensterecken und Browser-Knöpfe (biblix-design 2.2.1/2.3.0, biblix-browser 1.0.2).

## E: Leistungs-Overlay (biblix-design 2.3.0, biblix-system 1.3.0)

- MangoHud im Biblix-Look aus der Preset-Palette (`anwenden.overlay`): runde Ecken, Grund-Farbe als Hintergrund,
  Akzent für GPU/VRAM/Frametime, Akzent 2 für CPU/RAM, FPS rot/gelb/akzent ab 30/60. Startet **versteckt**
  (`no_display`), ein/aus mit **Shift rechts + F12**.
- Biblix Design → Animationen → „Leistungs-Overlay in Spielen“: Ausführlich (mit Frametime-Kurve, Watt, RAM/VRAM,
  „BIBLIX“) · Kompakt (eine Zeile) · Aus.
- Datei `~/.config/MangoHud/MangoHud.conf` mit Kopfzeile „# Biblix-Overlay“. Ohne diese Kopfzeile gilt sie als eigene
  Datei und wird nie überschrieben.
- Steam (Flatpak): Benutzer-Override `MANGOHUD=1` + `MANGOHUD_CONFIGFILE` (bei „Aus“ `MANGOHUD=0`). biblix-system
  installiert bei jedem Update den Baustein `org.freedesktop.Platform.VulkanLayer.MangoHud//<Zweig>` passend zu
  Steams Laufzeit (war auf dem echten PC nach dem Wechsel auf 26.08 nicht mehr da) und erlaubt
  `xdg-config/MangoHud:ro`.
- Einmalige Umstellung beim Anmelden: Einstellungs-Stand 6.

## F: Sofa-Modus mit dem Xbox-Controller (biblix-tools 1.5.0, biblix-bibiplexx 1.2.0)

- Gemeinsames Modul `/usr/share/biblix/gamepad/biblix_gamepad.py` (python3-evdev, liest alle Gamepads, neue alle 3 s).
  Nur das aktive Biblix-Fenster reagiert (ein Spiel im Vordergrund bleibt unberührt).
- Steuerkreuz/linker Stick: Auswahl wandert räumlich zum nächsten bedienbaren Element (gleiche Reihe zuerst),
  Scrollbereiche ziehen mit. A: auswählen · B: zurück/Dialog zu · X: Menü (Rechtsklick) · LB/RB: Bereich ·
  Start: Vollbild. Menüs und Auswahllisten bekommen echte Pfeiltasten.
- Auswahlrahmen erst nach dem ersten Tastendruck (Mausbedienung sieht aus wie vorher).
- **Bibiplexx:** LB/RB Saal/Serien/Filme, B zurück, Y „Überrasch mich“. Karten sind per Tab/Controller wählbar.
  Im Film (mpv `input-gamepad`): A/Start Pause, B Menü zu bzw. Ende, Steuerkreuz ±10 s und Lautstärke,
  LB/RB ±1 min, X Tonspur, Y Untertitel, Ansicht-Taste Bild-Infos.
- **S-Launcher:** LB/RB wechselt den Bereich links, B eine Seite zurück, A drückt Öffnen/Installieren/Spielen,
  Hausmarke-Karten sind wählbar.
- Getestet mit simulierten Tasten (offscreen); mit echtem Controller noch nicht.

## G: TMDB in Bibiplexx (biblix-bibiplexx 1.2.0)

- Eigener kostenloser Schlüssel (API-Schlüssel v3 oder Lese-Token v4, erkannt an „eyJ“) in den Einstellungen
  unter „Poster und Bewertungen (TMDB)“. Ohne Schlüssel bleibt alles wie bisher (Standbilder).
- **Poster** für Serien- und Filmkarten (2:3-Poster links, dahinter abgedunkelt), Folgen behalten ihr Standbild.
- **Bewertung** (★ 7,9, ab 5 Stimmen) auf den Karten und auf der Serienseite; Schalter „Bewertung anzeigen“ (an).
- **Beschreibung** optional (Schalter, aus): Serienseite, Saal-Leinwand (gekürzt), Tooltip.
- Cache: `~/.cache/bibiplexx/tmdb.json` und `tmdb/*.jpg`; Treffer monatlich, „nichts gefunden“ wöchentlich neu.
  Falscher Schlüssel → einmal Hinweis, dann keine Anfragen mehr bis zum Ändern.
- Hinweis laut TMDB-Bedingungen in den Einstellungen: „Verwendet die TMDB-API, ist aber nicht von TMDB unterstützt
  oder zertifiziert.“
- Selbst bei TMDB bewerten (mit TMDB-Konto) ist nicht eingebaut.
