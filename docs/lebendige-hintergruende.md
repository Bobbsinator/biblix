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
