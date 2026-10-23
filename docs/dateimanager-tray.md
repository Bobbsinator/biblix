# Dateimanager und Tray (23.10.2026, Wahl A / A)

## Tray-Symbole im Schrauben-Stil (biblix-design 2.2.0)

Lautstärke, Netzwerk (Kabel/WLAN), Bluetooth und Benachrichtigungen unten rechts als Bibi-Symbole:
Linien in Textfarbe, eine **Sechskant-Mutter in Akzentfarbe** als Erkennungszeichen
(Lautsprecher-Membran, Schraubenkopf beim Kabel, Mutter unter den Funkbögen, Klöppel der Glocke).

- Code: `lib/biblix_design/tray.py` (Motive), eingebaut ins Symbol-Thema (`symbole.py`, Ordner `scalable/status`,
  je Name auch `-symbolic`). Farben kommen aus der Preset-Palette.
- Design-App → Symbole → „Symbole unten rechts": **Bibi-Schrauben** (Standard) oder **KDE-Standard**.
- Geprüft im Test-Chroot mit Plasma (Kirigami.Icon wie im Tray). Ein eigenes Plasma-Thema war nicht nötig:
  Plasma 6 nimmt diese Symbole aus dem Symbol-Thema.
- Drehen beim Klick geht bei Tray-Symbolen nicht (Plasma zeichnet sie selbst).

## Dolphin (biblix-tools 1.4.0, Video-Aktion in biblix-bibiplexx 1.1.0)

**Orte in der Seitenleiste** (`biblix-orte`, Autostart bei der Anmeldung, und direkt nach „Platte einrichten"
in der Haustechnik): Bibiplexx (`/media/bibiplexx`), Spiele (`/media/spiele`), Daten (`/media/daten`),
OneDrive (`~/OneDrive`). Nur wenn der Ordner existiert, jeder nur einmal; selbst entfernte kommen nicht wieder
(Merker `~/.config/biblix/orte.json`). Windows-Platten bleiben unter „Geräte" (Klick bindet sie ein).
`biblix-orte --liste` zeigt den Stand.

**Rechtsklick → Bibi** (`usr/share/kio/servicemenus/biblix-*.desktop`, Helfer `/usr/lib/biblix/biblix-dateiaktion`):

| Aktion | Für | Was passiert |
|---|---|---|
| In Bibiplexx abspielen | Videos | `bibiplexx %F` |
| Als Hintergrund setzen | Bilder | `plasma-apply-wallpaperimage` |
| Bild verkleinern | Bilder | Kopie in halber Größe `name-klein.ext` (dreht Handyfotos richtig) |
| Als JPG / PNG / WebP speichern | Bilder | Kopie im anderen Format (JPG: Transparenz auf Weiß) |
| Als Admin öffnen (bibi) | Ordner | `dolphin admin:/pfad` über kio-admin (Passwort-Dialog) |
| Auf Windows-Platte kopieren … | alles | eingebundene NTFS-Platte wählen, Zielordner, Kopie mit KDE-Fortschritt |

Neue Empfehlungen in biblix-tools: `kio-admin`, `python3-pil`.
Ordnerfarben folgen schon dem Preset (Symbol-Thema).

## Prüfung vor dem Veröffentlichen (23.10.2026)

- Nach dem Update erzeugt `biblix-design anmeldung` das Symbol-Thema einmal neu (Einstellungs-Stand 4),
  damit die Tray-Symbole ohne Klick in der Design-App erscheinen.
- Bildaktionen: Format kommt aus dem Ziel (verkleinerte JPGs bleiben in Qualität 92), CMYK-Bilder werden
  nach RGB umgewandelt, GIF/HEIF/AVIF sind aus dem Menü genommen (Pillow kann sie nicht sauber).
- Haustechnik: „Secure Boot: aus" wird richtig erkannt (vorher „unbekannt"); das Einmal-Passwort geht über
  `openssl passwd -6 -stdin` statt über die Befehlszeile; Warte-Cursor beim Einrichten einer Platte.
- Neue Empfehlungen biblix-tools: `parted`, `openssl`.
