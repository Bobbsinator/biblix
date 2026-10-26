# Lebendige Hintergründe (biblix-design 2.4.0, 24.10.2026)

Plasma-Hintergrundmodul **`de.biblix.lebendig`** (`usr/share/plasma/wallpapers/de.biblix.lebendig`), 24 animierte
Szenen in QML (Qt Quick, Partikel, Shapes), alle in den Farben von Biblix Design. Kein Shader-Werkzeug nötig.

- **Auswahl:** Biblix Design → Hintergrund → „Lebendig (animiert)“ (Vorschaubilder in `usr/share/biblix/design/lebendig/`).
  ID im Design: `lebendig-<szene>`. Auch über „Hintergrundbild einrichten“ von Plasma (Szene, Tempo, Pause).
- **Szenen:** Sternenflug, Sternenhimmel, Glühwürmchen, Schnee, Regen, Bokeh, Farbnebel, Wellen, Tropfen,
  Schwebende Muttern, Leuchtwaben, Muttern-Tunnel, Stromkreis, Equalizer, Synthwave, Prompt mit Bibi-Sprüchen
  (`sprueche.txt`), Bauplan; Firmen-Szenen in Firmenfarben: Tower bei Nacht und Wafer (Bibi Tech), Zugriffsindex
  (Bibi Budget Bank), Route (Bibi Delivery), Lächelbögen (Bibi Mac), Donau-Abend (Nassmacher), Saallichter (Bibiplexx).
- **Leistung:** Pausiert, solange auf dem Bildschirm ein Fenster maximiert oder im Vollbild ist (Spiele).
  Gemessen: ca. 3 % eines CPU-Kerns für ganz Plasma, der Rest läuft auf der Grafikkarte.
- **Sperrbildschirm und Vorschau** nehmen ein passendes Standbild (`hintergruende.LEBENDIG`, 4. Spalte).
- **Neue Szene:** `szenen/<name>.qml` erbt von `Szene.qml` (Farben `f`, `laeuft`, `tempo`, `sprueche`, Hilfen `c()`,
  `mix()`, `zufall()`), Bausteine `Licht.qml` (weicher Lichtfleck) und `Sechseck.qml`; Eintrag in
  `hintergruende.LEBENDIG` und `config.qml`, Vorschaubild 300×169 dazu.
- **Stolperfallen:** Qt 6 kennt kein `by` bei NumberAnimation (eigene Versatz-Eigenschaft animieren). Plasma behält
  geladene QML-Dateien im Speicher: zum Testen `systemctl --user restart plasma-plasmashell`. `filterMinimized` zusammen
  mit Bildschirm-/Arbeitsflächenfilter liefert in Plasma 6.3 eine leere Liste, daher selbst auf `IsMinimized` prüfen.

## Video-Szenen aus Blender (biblix-design 2.6.0, 26.10.2026)

- Erste Video-Szene **„Tower im Regen“** (`regenfahrt`): Kamerafahrt einmal um den Exabibi Tower bei Nacht und Regen,
  10 s, 4K, nahtlose Schleife. Szene `szenen/regenfahrt.qml` spielt `contents/videos/exatower-regen.mp4` mit
  QtMultimedia (ohne Ton, `PreserveAspectCrop`), pausiert wie alle Szenen. Bis das erste Bild da ist, liegt
  `exatower-regen.jpg` darüber. Paket hängt deshalb von `qml6-module-qtmultimedia` ab.
- **Quellen:** `kunst/blender/` (`hilfen.py`, `exatower_szene.py`, `exatower_regenfahrt.py`, Standbild `exatower_nacht.py`).
  Render-Ausgaben nach `kunst/ausgabe/` (nicht im Git). Neu erzeugen:
  ```
  cd kunst/blender && BILDER=240 BREITE=3840 HOEHE=2160 blender -b --factory-startup -P exatower_regenfahrt.py -- ../ausgabe/regenfahrt4k/bild_
  ffmpeg -framerate 24 -i ../ausgabe/regenfahrt4k/bild_%04d.png -c:v libx264 -crf 24 -preset slow -pix_fmt yuv420p -movflags +faststart -an exatower-regen.mp4
  ```
- **Blender auf Biblix:** Das Debian-Blender (4.3) kann Cycles nur auf dem Prozessor und ohne Entrauschen; EEVEE läuft
  über die Grafikkarte (die ganze 4K-Fahrt in wenigen Minuten). Für Videos daher EEVEE nehmen.
- Video-Szenen stehen in `hintergruende.LEBENDIG` mit einem Standbild `datei:<pfad>`; `LEBENDIG_NEU` markiert neue.
