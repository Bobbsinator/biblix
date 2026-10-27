# Biblix-Zeremonien (biblix-zeremonien 1.0.0, 27.10.2026)

Komplett übertriebene Filme beim Anmelden, Abmelden und Ausschalten. Eigenes Paket `biblix-zeremonien`
(Player `biblix-zeremonie`, Filme in `/usr/share/biblix/zeremonien/`), vom Sammelpaket `biblix` (1.5.0) gezogen.

| Film | Wann | Stil | Inhalt (Kanon-Bezug) |
|---|---|---|---|
| `hochfahren` | erste Anmeldung nach dem Systemstart (boot_id) | Blender 3D, Industrie | Big Bibi fährt von -8 nach 0, Hebel AUF – HALT – AB, Tore, „AUF BIBLIX GEHT DAS.“ (6.1) |
| `keynote` | jede weitere Anmeldung | Blender, Bühnenlicht | Countdown, Claim von Bibi Tech, „Dein Desktop“, Budget 80 → 240 Mio, GENEHMIGT. (8.1, 8.4) |
| `abmelden` | Abmelden im Bibi-Startmenü | Blender, Nacht/Regen-Asphalt | Statuskette, Bastionswürfel BDW-B lädt die Fenster ein (9.3) |
| `herunterfahren` | Ausschalten im Bibi-Startmenü | Blender, warmes Stimmungsbild | Monatsabschluss: Fallblatt-Tafel, Hauptbuch, Stempel „ZUR KENNTNIS GENOMMEN.“ (BBB 4/5) |
| `windows` | Neustart in Windows | Retro-Terminal (Pillow) | „FREMDES SYSTEM ERKANNT“, „Netter Versuch.“, „VIEL ERFOLG.“, „DEIN SYSTEM. DEIN PROBLEM.“ (8.6) |

- **Bedienung:** jede Taste/Klick überspringt, **Esc bricht Abmelden/Ausschalten/Windows-Neustart ab**. Im Spielmodus
  (gamemoded aktiv) nie. Biblix Design → Sperrbildschirm und Start → Zeremonien: Voll / Kurz (letzte 3 s) / Aus,
  dort auch „Zeremonien ansehen …“.
- **Ablauf:** Bibi-Startmenü ruft `biblix-zeremonie abmelden|herunterfahren` auf (wenn das Paket da ist), der Player
  spielt den Film und ruft danach KDE (`org.kde.Shutdown.logout` / `logoutAndShutdown`). Das KDE-Bestätigungsfenster
  entfällt dabei; der Film ist die Bestätigung (Esc = abbrechen). `biblix-neustart-windows` (biblix-tools 1.6.1)
  zeigt den Film nach der Rückfrage und vor dem Umstellen des Bootmenüs.
- **Nicht** beim reinen Systemstart (Plymouth kann keine Videos und wäre nur Sekunden zu sehen): Big Bibi läuft deshalb
  direkt nach der ersten Anmeldung. Neustart (normal) hat keinen Film.
- **Quellen:** `kunst/blender/zeremonien/*.py` (EEVEE), `kunst/zeremonien/windows.py` (Pillow), Ton
  `kunst/zeremonien/klaenge.py` (Synthese), Titelkarte `titel.py`. Neu erzeugen: `kunst/zeremonien/alle_rendern.sh`,
  dann `kunst/zeremonien/zusammensetzen.sh` (schreibt die MP4 ins Paket).
- Bibis selbst sind nicht im Bild (keine Figuren nach Visual Standard in Blender); Szenen = Gestaltung, kein Kanon.
