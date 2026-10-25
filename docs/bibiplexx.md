# Bibiplexx (biblix-bibiplexx 1.0.0)

Entscheidungen vom 22.10.2026:

- **Technik A**: eigene Sammlungs-Oberfläche (PyQt6), gespielt wird im Vollbild mit **mpv**
  (`--include` eigene Einstellungen, `--script` eigene Steuerleiste; die mpv.conf des Nutzers bleibt unberührt).
- **Extras im ersten Update**: Weiterschauen, Kinomodus. (Streaming-Kacheln und Snack-Theke bewusst nicht.)
- **Filmplatte**: die frei gewordene Samsung 840 EVO (altes Windows, unter Windows gelöscht) wird in Biblix
  über den Assistenten als `/media/bibiplexx` eingerichtet.

## Funktionen (Stand 1.0.0)

- **Saal**: Leinwand mit Weiterschauen bzw. Neuem, „Überrasch mich" (ungesehener Film oder nächste Folge), Reihen.
- **Rechtsklick** auf Karten: abspielen, von vorn, gesehen/ungesehen (auch ganze Serie), aus Weiterschauen entfernen, im Dateimanager zeigen.
- **Filme sortieren**: A–Z, zuletzt hinzugefügt, Erscheinungsjahr. Sammlung wird beim Zurückkommen ins Fenster neu eingelesen (max. 1×/Min.).
- **Player**: Steuerleiste mit Zeitvorschau beim Spulen, **Intro überspringen** (Kapitel Intro/Vorspann/Recap/Rückblick),
  **„Nächste Folge in …"** mit Jetzt/Abbrechen (Ende oder Abspann-Kapitel), **Schlaf-Timer** (nach der Folge, 30/60/90 Min.,
  danach leise ausblenden und „Gute Nacht."), **Nachtmodus** (dynaudnorm), Tasten T/N/F.
- **Einstellungen**: Kinomodus (Vorhang + Gong / nur Vorhang / aus), Nachtmodus, Tonspur (Deutsch zuerst / Original),
  Untertitel (nur bei fremder Sprache / immer deutsch / aus), Untertitel-Größe und -Farbe (Weiß / Kino-Gelb),
  nächste Folge automatisch, Countdown 10/15/25 s/aus, Intro-Knopf an/aus. HDR wird an KDE weitergereicht (`target-colorspace-hint`).

## Aufbau

| Datei | Zweck |
|---|---|
| `usr/share/biblix/bibiplexx/bibiplexx.py` | Sammlung: Saal (Leinwand + Reihen), Serien, Filme, Suche, Einstellungen, Platten-Assistent |
| `usr/share/biblix/bibiplexx/mpv/bibiplexx.lua` | Steuerleiste, Vorhang-Intro mit Gong, Fortschritt nach `~/.local/state/bibiplexx/fortschritt.json` |
| `usr/share/biblix/bibiplexx/mpv/bibiplexx.conf` | mpv-Einstellungen (gpu-next, hwdec, deutsche Spuren zuerst, max. 100 % Lautstärke) |
| `usr/lib/biblix/bibiplexx-platte` | richtet nur **komplett leere** Platten ein (pkexec, Policy `de.biblix.bibiplexx-platte`) |
| `usr/share/biblix/hausmarke.d/bibiplexx-app.json` | ersetzt den „In Arbeit"-Platzhalter in der Hausmarke Bibi |

Standbilder erzeugt `ffmpeg` (12 % der Laufzeit) nach `~/.cache/bibiplexx/plakate/`; liegt `poster.jpg`,
`folder.jpg` oder `<Dateiname>.jpg` daneben, wird das genommen.

## Lore

Nur vorhandene Lore genutzt: „Reihe sieben." im Intro, „BEREITS REFERENZPEGEL." beim Versuch, über 100 %
zu drehen. **Kein süßes Popcorn**, nirgends, auch nicht als Option.

## 1.0.1 (22.10.2026, Prüfung)

- Schlaf-Timer „nach der Folge" beendet auch dann, wenn Countdown oder „Nächste Folge" weiterschalten.
- Während des Vorhangs wird die gespeicherte Stelle nicht mehr mit 0 überschrieben.
- Jahreszahlen: die letzte plausible zählt („Blade.Runner.2049.2017" → „Blade Runner 2049", 2017).
- Nach dem Film zurück zur gleichen Serie; beim Schließen wird das Einlesen sauber beendet.

## 1.1.0 (23.10.2026): Bild, Sprache, Qualität

- **Bild-Infos** (Taste I): Auflösung, Bildrate und Bildschirm-Hz, Bildglättung, Codec, HDR10/HLG/SDR,
  Dekodierung (Grafikkarte/Prozessor), Bitrate, verlorene Bilder, Tonspur, Qualitätsstufe.
- **Bild-Menü** (Taste B): Bildglättung, Bild füllen (ohne schwarze Ränder), Debanding, Grafikkarten-Dekodierung.
- **Sprache-Menü** (Taste L): alle Ton- und Untertitelspuren mit Namen („Englisch · 5.1 · AAC · Original").
- **Automatische Sprache: Englisch** (Ton und Untertitel; Wunsch 23.10.). In den Einstellungen umstellbar auf
  Deutsch, Japanisch oder Originalton. Untertitel „nur bei fremder Sprache": bei englischem Ton keine.
- **Qualität „Höchste"** (Standard): `profile=high-quality`, ewa_lanczossharp, Debanding, HDR-Spitzenmessung,
  Grafikkarten-Dekodierung (auto-safe). „Ausgewogen" = `profile=fast`.
- **Bildglättung** (Standard an): `video-sync=display-resample` + Interpolation, damit 24/25-fps-Filme auf 240 Hz
  nicht ruckeln. Kennt mpv die Bildschirmrate nicht, schaltet Bibiplexx die Glättung nach 2 s selbst ab (sonst
  bliebe das Bild schwarz).
- Karten und Folgen zeigen die Qualität („1080p · 25 fps", „4K · HDR") per ffprobe.
- Rechtsklick in Dolphin → Bibi → **In Bibiplexx abspielen** (`usr/share/kio/servicemenus/biblix-video.desktop`).
- Prüfung: alte Einstellungen (Stand 1, speicherten immer „deutsch") werden einmal auf Englisch umgestellt;
  Bildglättung lässt sich ohne bekannte Bildschirm-Hz nicht einschalten (Meldung statt schwarzem Bild);
  Bitrate zeigt bis zur ersten Messung den Schnitt der Datei; bei vielen Untertiteln bleibt „Aus" sichtbar.

## 1.3.0 (25.10.2026): Importieren und Ranking

**Import-Assistent** (`importieren.py`, Knopf „Importieren" oben, `bibiplexx --importieren [ORDNER]`,
Dolphin: Rechtsklick auf einen Ordner → Bibi → „In Bibiplexx importieren"):

- Quelle wählen: angesteckte Platten (unter `/media/<name>/`, erscheinen von selbst) oder ein Ordner.
- Erkennung wie in Bibiplexx (`S01E02`, `1x02`, Jahr), dazu: Serienname aus dem Ordner
  („Die Simpsons/Staffel 3/03x05 …"), Filmtitel und Jahr aus dem Ordner bei Release-Ordnern
  („Inception.2010.1080p…/sparks-inception.mkv"), kleingeschriebene Namen werden groß geschrieben.
  Samples und `System Volume Information` werden übersprungen.
- Vorschau alt → neu, Name und Jahr direkt änderbar; was schon in Bibiplexx ist (gleiche Serie/Staffel/Folge
  bzw. Film), ist „schon da" und abgehakt; zwei Dateien mit demselben Ziel (720p und 1080p) → nur eine.
  Unklare Einzeldateien (Film ohne Jahr) stehen unter „Unklar" mit Auswahl Film/Serienfolge (Staffel, Folge).
- Mit TMDB-Schlüssel: richtiger Name, Jahr, Folgentitel; „Meintest du …?" als Auswahl (bis zu 6 Treffer).
  Sprache der Titel folgt der Tonsprache (Deutsch → de-DE, sonst en-US).
- Ablage wie gehabt: `Serien/Name (Jahr)/Staffel N/Name - S01E02 - Titel.mkv`, `Filme/Titel (Jahr)/Titel (Jahr).mkv`;
  vorhandene Serienordner werden weiterbenutzt. Untertitel (`Name.de.srt`, `Subs/`) kommen mit.
- **Nur kopieren**, Originale bleiben. Platzprüfung (2 GB Reserve), Fortschritt mit Restzeit, Abbrechen.
  Kopiert wird nach `Datei.bibiplexx-teil` und erst am Ende umbenannt (abgezogene Platte → keine halbe Datei).
- Danach „Platte sicher entfernen" (udisksctl unmount + power-off).

**Wächter** (`waechter.py`, Autostart `/etc/xdg/autostart/de.biblix.Bibiplexx.Waechter.desktop`, ohne Qt):
schaut alle 3 s nach neuen Wechselplatten, hängt sie ein (udisksctl, ohne Passwort) und fragt per Meldung
„Auf „HDD" gibt es 3 neue Folgen und 1 neuen Film. In Bibiplexx übernehmen?" → Importieren / Nicht jetzt.
Platten, die beim Anmelden schon steckten, bleiben in Ruhe. Abschaltbar: Einstellungen → „Beim Anstecken einer Platte fragen".

**Ranking** (neuer Bereich, `ranking.py`, gespeichert in `~/.local/state/bibiplexx/ranking.json`):

- **Tierlist** S–D zum Ziehen: S „Reihe sieben", A „Salziges Popcorn", B „Läuft", C „Nebenbei am Handy",
  D „Im Saal eingeschlafen". Filter Serien/Filme, „Als Bild speichern" (`~/Bilder/Bibiplexx-Tierlist-DATUM.png`).
- **Top 10** Serien und Filme, mit ▲ ▼ sortieren, Platz 1–3 in Gold, Silber, Bronze.
- **Meine Sterne** (1–5, eigene Bewertung neben der TMDB-Note); erscheinen auch auf den Karten (pink, oben links).
- Alles auch per Rechtsklick auf Karten und Poster. Controller: LB/RB schaltet jetzt auch zum Ranking.
