# S-Launcher-Welten (biblix-tools 1.3.0)

Entscheidungen vom 22.10.2026 (Variante E „Welten“):

- **Grundaufbau Schaufenster**: großer animierter Kopf auf der Startseite, Kacheln blenden weich ein,
  Prompt-B-Logo mit blinkendem Cursor, Welt-Knopf (Schraubenmutter) oben rechts.
- **Welt-Knopf**: Welt (Automatisch = folgt Biblix-Design-Preset, oder fest), Animationen
  (voll / dezent / aus), Klänge an/aus. Gespeichert in `~/.config/biblix/s-launcher.json`.
- **Kategorie „Hausmarke Bibi“** (Name gewählt: C). Einträge kommen aus
  `/usr/share/biblix/hausmarke.d/*.json`; neue Bibi-Apps legen dort per Update ihren Eintrag ab.
  Ein fertiger Eintrag ersetzt einen gleichnamigen Platzhalter mit `"status": "in_arbeit"`.
- **Bibiplexx**: Platzhalter-Kachel „In Arbeit“, nicht anklickbar (Option A), bis die App kommt.

## Welten

| Welt | Preset | Seitenwechsel | Besonderheiten |
|---|---|---|---|
| Schaufenster | alle übrigen | Blende | schwebendes Prompt-B |
| Tower | Bibi Tech | Aufzugtüren mit Stockwerk | Etagen EG–5, Haustechnik im UG, Stockwerksanzeige, Tower mit Lichtern und Aufzug, Aufzug-Ding |
| Bestelltheke | Bibi Mac | Schieben | „Bestellen“ statt Installieren, Bestellnummer und Abholanzeige, Kassa- und Abholton |

Geplant per späterem Update: Lieferung (Delivery), Kino (Bibiplexx), Tresor (Budget Bank), Rutsche (Nassmacher).

Code: `pakete/biblix-tools/usr/share/biblix/s-launcher/welten.py`; Klänge werden beim Bauen in
`vorbereiten.sh` synthetisiert (WAV, abgespielt mit `pw-play`/`paplay`).
