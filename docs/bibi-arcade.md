# Bibi Arcade (biblix-arcade)

Spielebibliothek im Stil eines Rechenzentrums. Start: S-Launcher → „Bibi Arcade“, Startmenü oder
`bibi-arcade` (`--vollbild` fürs Sofa). Gewählt am 25.10.2026: Rechenzentrum + Datenblatt + Netz.

## Bereiche

- **RACK** – jedes Steam-Spiel ist ein 1U-Einschub. Spalten: U-Nummer, zwei LEDs (Linux-Ampel, Aktivität),
  Etikett, Klebeband mit Gesamtzeit, Last der letzten 2 Wochen, zuletzt gespielt. Der gewählte Einschub fährt
  heraus. Läuft ein Spiel, blinkt die zweite LED und darunter steht „IN BETRIEB“. Spiele mit Anti-Cheat-Sperre
  blinken rot, nicht fertig geladene stehen auf „WARTUNG“. Rechts: Cover, Knopf, Systemprotokoll.
- **DATENBLATT** (X, Leertaste, Rechtsklick) – Blaupause mit Maßlinien, Prüfstempel (GEPRÜFT / BEDINGT /
  UNGEPRÜFT / NICHT FREIGEGEBEN / WARTUNG), Werten, Wochenbalken und Schriftfeld. Bei Anti-Cheat rot mit
  „In Windows starten“ (nutzt `biblix-neustart-windows`) und „Trotzdem starten“.
- **NETZ** – lebendiges Netzwerk um **DU**: Nähe = zuletzt gespielt, Rand = Linux-Ampel, oranger Ring =
  Anteil an der gesamten Spielzeit. **Spielart-Knoten** (Sechsecke aus dem Steam-Shop, ab zwei Spielen; ohne
  Action/Indie/Early Access) verbinden verwandte Spiele, der **Labor-Knoten** trägt die Bibi-Spiele (Enter startet
  sie). **Datenpakete** fliegen von DU zu den Spielen – mehr Verkehr bei viel Spielzeit in den letzten 2 Wochen, ein
  laufendes Spiel bekommt einen orangen Strom. Beim ersten Öffnen fliegen alle Knoten aus DU heraus. Gewählter
  Knoten: Nachbarn hell, Rest gedimmt; Infokasten mit Anteil, Spielart, verwandten Spielen und Wochenbalken.
  Größe umschaltbar (G, Ansicht-Taste, Knopf): Spielzeit / letzte 2 Wochen / Speicher. Mausrad zoomt um den
  Mauszeiger, Hintergrund ziehen verschiebt, Knoten lassen sich ziehen, 0 = mittig, S = Spielarten an/aus,
  E = einladen. Jeder Knoten hat ein unsichtbares Fokus-Widget (Controller/Pfeile springen von Knoten zu Knoten).
- **LABOR** – Prüfstände für eigene Bibi-Spiele (siehe unten), mit Pause, Ergebnis und Bestwerten.

## Einladen

📨 EINLADEN im Rack (Taste E) und im Datenblatt. Vorlagen: Heute Zeit?, Fester Termin, Jetzt sofort,
Wann passt's?, Wochenende, Neues Spiel (mit Spielart und Linux-Ampel), Revanche, Eigener Text – jeweils in
du- und ihr-Form (ein Freund: „Hey Max“, mehrere: „Hey Leute … habt ihr“). Tag (heute bis +6) und Uhrzeit
wählbar, Shop-Link optional, Text frei änderbar.

- **Freunde**: aus Steams eigenem Zwischenspeicher (`localconfig.vdf` → `friends`: Name, Bild-Kennung),
  Profilbilder von `avatars.steamstatic.com` (nur mit „Online prüfen“, gemerkt in `~/.cache/bibi-arcade/avatare`).
  Zuletzt Eingeladene sind vorgewählt (`~/.local/share/bibi-arcade/einladungen.json`).
- **Steam-Chat**: pro Klick ein Freund – persönliche Einladung in die Zwischenablage, dann
  `steam://friends/message/<SteamID64>`. **WhatsApp**: Text kopieren und ZapZap öffnen (sonst web.whatsapp.com).
- **Einladungskarte** 1200 × 630 im Datenblatt-Stil (Cover, WANN/WO/LINUX/VON/AN, Stempel je Vorlage):
  kopieren (Bild in der Zwischenablage) oder in `~/Bilder` speichern.
- Abgeschickt wird nie automatisch: Strg+V und Enter macht der Nutzer selbst.

## Bibi-Spiele (im Paket)

- **Bibi Minesweeper** (`spiele/bibi_minesweeper`) und **Bibi Solitär** (`spiele/bibi_solitaer`), je drei Stufen,
  gebaut in einem eigenen Chat (Zweig `arcade-spiele` in `~/biblix`), übernommen am 25.10.2026.
  Eigene Klänge als WAV; QtMultimedia wird genutzt, wenn vorhanden, sonst pw-play/paplay/aplay.
- Unten in der Arcade stehen während eines Spiels die Spiel-Tasten statt der Rack-Tasten.

## NOT-AUS

Läuft ein Spiel, erscheint im Rack und im Datenblatt ein roter Knopf **⏻ NOT-AUS** (Tastatur: Entf auf dem
Einschub). Nach einer Nachfrage (Standard: Abbrechen) bekommt das Spiel SIGTERM, was nach 4 s noch lebt SIGKILL.
Getroffen werden nur Prozesse, deren Programm (argv[0]) aus `steamapps/common/<Ordner>/` kommt – unter Proton
der Windows-Pfad – oder die Steam als dieses Spiel markiert hat (`SteamAppId`, `SteamGameId`,
`STEAM_COMPAT_APP_ID` in der Umgebung). Steam selbst (`steam`, `steamwebhelper`) und die Arcade bleiben verschont,
ebenso Programme, die den Ordner nur im Befehl erwähnen (Dateimanager, Konsole). Dieselbe argv[0]-Regel gilt
für „IN BETRIEB“. Getestet mit Schein-Prozessen (auch einem, der SIGTERM ignoriert) und Lockvögeln.

## Daten

- Steam (Flatpak oder normal) wird nur gelesen: `libraryfolders.vdf`, `appmanifest_*.acf`,
  `userdata/*/config/localconfig.vdf` (nur Abschnitt `apps`: Playtime, Playtime2wks, LastPlayed),
  `appcache/librarycache/<appid>/` (Cover, Hero, Logo). Proton, Steam Linux Runtime und Steamworks werden ausgeblendet.
- Linux-Ampel: ProtonDB-Zusammenfassung pro Spiel, Anti-Cheat-Liste von AreWeAntiCheatYet (ganze Liste),
  Spielarten aus dem Steam-Shop. Abschaltbar (⚙ → „Online prüfen“). Merkdauer 7 bzw. 28 Tage,
  in `~/.cache/bibi-arcade/`.
- Wochenbalken: Steam kennt nur Gesamtzeiten, die Arcade merkt sich bei jedem Start den Tagesstand
  (`~/.local/share/bibi-arcade/verlauf.json`, ein Jahr).
- „Läuft gerade“: argv[0] eines Prozesses liegt in `steamapps/common/<Ordner>/` (auch unter Proton).
- Einstellungen `~/.config/biblix/arcade.json` (Geräusche, Hochfahren, Online prüfen, Sortierung).
- Geräusche werden beim ersten Mal berechnet (`klang.py`) und mit `pw-play` leise abgespielt.

## Controller

A starten · B zurück · X Datenblatt · Y suchen · LB/RB Rack/Netz/Labor · Ansicht-Taste sortieren · Start Vollbild.
Tastatur: Pfeile, Pos1/Ende, Bild auf/ab, Enter starten, Leertaste oder → Datenblatt, Strg+Tab Bereich, F2 sortieren, F5 neu laden, F11 Vollbild.
Während ein Bibi-Spiel läuft, gehen die Tasten ans Spiel: Steuerkreuz = Pfeile, A = Enter,
X = Leertaste, Y = Backspace, B = Pause.

## Schnittstelle für Bibi-Spiele

Ordner `spiele/<kennung>/` in `/usr/share/biblix/arcade/` (Paket), `~/.local/share/bibi-arcade/` (eigene)
oder `$BIBI_ARCADE_SPIELE` (zum Testen):

- `spiel.json`: `{"kennung", "name", "kurz", "version", "stufen": [...]}`
- `spiel.py`: `class Spiel(QWidget)` mit `__init__(umgebung)` (`{"stufe", "ton", "speicher": Path}`),
  `fertig = pyqtSignal(dict)` (`{"gewonnen", "punkte", "zeit", "stufe"}`), `starten(stufe)`, `pausieren()`,
  `fortsetzen()`. Nur Python 3 + PyQt6, alles mit QPainter, skaliert auf jede Größe.
- Escape gehört der Arcade (Pausenmenü). Ein kaputtes Spiel bringt die Arcade nicht zum Absturz: der
  Prüfstand zeigt „DEFEKT“, der Fehler steht im Systemprotokoll.
- Bestwerte je Stufe: `~/.local/share/bibi-arcade/bestwerte.json`; Spielstände unter `spielstaende/<kennung>/`.

## Testen (ohne den Nutzer zu stören)

`QT_QPA_PLATFORM=offscreen` mit `BIBLIX_KONFIG_DIR`, `BIBI_ARCADE_DATEN`, `BIBI_ARCADE_CACHE`,
`BIBI_ARCADE_SPIELE` und `BIBI_ARCADE_SCHRIFTEN` (Ordner mit IBM-Plex-TTFs, falls fonts-ibm-plex fehlt),
dann Seiten mit `grab()` als PNG speichern.
