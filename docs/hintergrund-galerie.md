# Hintergrund-Galerie und Standorte (biblix-design 2.5.0, 25.10.2026)

## Galerie (Biblix Design → Reiter „Hintergründe“)

- **Monitore oben:** Hauptmonitor = Plasma-Bildschirm 0 (auch Sperrbildschirm), „Weitere Monitore“ = alle anderen.
  Klick auf einen Monitor markiert das Ziel; Doppelklick auf ein Motiv setzt es dort. Beim Drüberfahren über eine Kachel:
  Knöpfe Haupt / Weitere / Alle. „Alle Monitore gleich“ koppelt beide.
- **Diashow:** Gruppe wählbar (Gruppe des Hauptbildes, Standorte, Biblix, je Firma, eigene Bilder), Minuten, „nur Hauptmonitor“.
- **Eigene Bilder:** einzelne Dateien (`datei:/pfad`) oder Ordner (`ordner:/pfad`, läuft als Diashow des Ordners).
  Gespeichert in `eigene_bilder`; eigene Bilder gehen nie an den Systemhelfer (Bootmenü/Anmeldung bekommen dann den Standard).
- **Farben:** Firmenmotive in Firmenfarben oder in der aktuellen Palette (`hintergrund_eigene_farben`). Standorte haben feste Farben.

Neue Einstellungen in `kern.STANDARD`: `hintergrund_zweiter`, `hintergrund_eigene_farben`, `eigene_bilder`,
`diashow_gruppe`, `diashow_monitore`. Anwenden: `anwenden.hintergrund()` schreibt ein Plasma-Skript pro Desktop
(`d.screen <= 0` → Hauptmonitor).

Code: `app/galerie.py` (Seite), `lib/biblix_design/hintergruende.py` (Motive, eigene Bilder), `lib/biblix_design/standorte/`.

## Standorte

| ID | Ort | Stil |
|---|---|---|
| standort-tower | Exabibi Tower, Schnitt 94 OG bis Bibi Tief, Detail A (Aufzug hält nicht in 93) | Bauplan |
| standort-bank | BBB-BGLD Zugriffshalle, Fallblatt-Knappheitstafel | Messing, Marmor, grüne Lampen |
| standort-mac | Bibi Mac am Bibi Boulevard, Menütafel ohne Preise (Grundbedarf kostet nichts) | Rot-Gelb-Creme |
| standort-delivery | Delivery W, alle acht Würfel BDW-F … BDW-B, Statuskette | Typentafel Blau-Gelb |
| standort-nassmacher | Parkplan: Rutsch und Flutsch, Hohe See, River, Kleine Donau, Bowlhafen, Saunawelt | bunt, sommerlich |
| standort-plexx | Saalplan mit Direct-View-Wand, Reihe sieben, KI-Soundsystem | Kino, dunkel |
| standort-burgenland | Ebenenplan 0 bis -8, Big Bibi, BZB | Brigade, Anthrazit |
| standort-hh | Mobile IT-Werkstatt, Crimpzangenpflicht, E 1024 E | hell, Referenzblatt |

Regeln: Alle Texte aus dem Masterbrief; Anordnungen (Parkplan, Sitzreihen, Abholnummern) sind Design, kein Kanon.
Nicht eingezeichnet: Euro-Tresor „der Berg“ und Ebene -9. Keine echten Markenlogos.

**Nächste Serien stilistisch mischen** (Wunsch des Nutzers): Stimmungsbilder mit Licht/Nebel/Körnung, Isometrie,
Pixel-Art, Retro-Poster, animierte Szenen, 3D (Blender, falls installiert) – nicht wieder nur Pläne und Tafeln.

Neues Standort-Motiv: Modul in `standorte/` mit Funktion `motiv(p=None) -> SVG`, Eintrag in `standorte.STANDORTE`.
