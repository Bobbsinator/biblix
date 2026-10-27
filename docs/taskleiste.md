# Taskleiste „Typenschild“ (biblix-design 2.7.0, 27.10.2026)

Standard ab 2.7.0: eigene **Biblix-Fensterleiste** (`de.biblix.leiste`) und **Biblix-Uhr** (`de.biblix.uhr`) statt
KDE-Fensterleiste und Digitaluhr; Startknopf = **gelber B-Knopf** (`de.biblix.startmenue`, `knopf=bknopf`).
Biblix Design → Taskleiste: Stil *Typenschild* / *Klassisch (KDE)*, Schalter *Lack*, Schalter *Welten*.

## Fensterleiste
- Jede App in derselben Fassung, aktives Fenster mit Rahmen + LED, **Muttern zählen die offenen Fenster** (max. 4),
  wer Aufmerksamkeit will, blinkt. Fortschritt (Downloads) über die Smart-Launcher-Schnittstelle (`Fortschritt.qml`,
  optional geladen); in der Delivery-Welt als Statuskette.
- Bedienung wie KDE (TasksModel): Klick aktiviert/minimiert, bei mehreren Fenstern der Reihe nach; Mittelklick = neues
  Fenster; Rechtsklick: Neues Fenster, Anheften/Lösen, Schließen. Angeheftete Apps werden beim Umstellen übernommen.
- **Lack** (`lack`): alle Symbole einfarbig in der Akzentfarbe (MultiEffect), das aktive Fenster in echten Farben.
- **Welten** (`welt`, folgt dem Preset, bei eigenen Farben „typenschild“):
  bibi-tech → `tower` (runde Stahlknöpfe, Uhr als Etagenanzeige) · bank → Messingrahmen, Fallblatt-Uhr ·
  mac → runde Creme-Knöpfe, Uhr als Abholnummer · delivery → blaue Kacheln, Statuskette · plexx → Kinoschild-Uhr mit
  Lichtern · nass → Schwimmreifen-Knöpfe, Uhr als Badekappe. B-Knopf-Farbe je Welt (`anwenden.WELT_KNOPF`).

## Instrumentenfeld
- `de.biblix.instrumentenfeld` steht direkt vor dem Systemabschnitt (Lautstärke, Bluetooth, Netzwerk …) und zeichnet
  darunter eine eingelassene Fassung, so breit wie der rechte Nachbar (sucht ihn im Leisten-Layout, Container `z = -1`).
  Der Systemabschnitt selbst bleibt der von KDE. Je Welt: Schrauben (Typenschild, Tower, Bank), Messing (Bank),
  Kinolichter (Bibiplexx), Beckenrand (Nassmacher) …
- Biblix Design setzt es beim Typenschild automatisch ein und nimmt es beim Stil „Klassisch“ wieder heraus.

## Noch nicht drin (bewusst, spätere Updates)
- Fenstervorschau beim Drüberfahren (nur Tooltip mit Titel), Umsortieren per Ziehen, Dateien auf Apps ziehen.
- Der Leistenhintergrund selbst folgt weiter dem Plasma-Stil in Preset-Farben (kein Stahl-/Messingverlauf).
- Beim ersten Umstellen baut Biblix Design die Leiste neu auf: ausgeblendete Symbole unten rechts gehen dabei auf Standard.

## Testen ohne Paket
Plasmoids nach `~/.local/share/plasma/plasmoids/` kopieren (überschreibt die Systemversion), `systemctl --user restart
plasma-plasmashell`, per Plasma-Skript auf einer Leiste einsetzen. Danach die Kopien wieder löschen.

## Umstellung beim Update
`biblix-design anmeldung` stellt einmalig (`_stand` 7) beim nächsten Anmelden auf das Typenschild um (beide Monitore,
angeheftete Apps bleiben). Rückweg: Biblix Design → Taskleiste → Stil „Klassisch (KDE)“ → Übernehmen.
Live geprüft am 27.10.2026: Umbau hin und zurück, zweiter Lauf ändert nichts.

## 2.7.1 (27.10.2026)
Knöpfe kleiner (Typenschild 80 %, rund 76 %, Fahrstuhl mit Metallring 68 % der Leistenhöhe), Hover nur noch 4 %,
B-Knopf 80 % mit kleinerem Schein: nichts ragt mehr aus der Leiste und wird abgeschnitten.
