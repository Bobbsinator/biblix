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
