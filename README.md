# Biblix 1.0

**DEIN SYSTEM. DEIN PROBLEM.**

Biblix ist ein echtes, installierbares Linux auf Basis von **Debian 13
„trixie"** mit **KDE Plasma 6**, im Look von Bibi OS. Es enthält den
**S-Launcher** als App-Browser, **Steam** für Spiele sowie vorbereitete
Treiber für **NVIDIA und AMD**, abgestimmt auf **Ryzen 7 9800X3D + RTX 5070 Ti**.

---

## Was drin ist

| Bereich | Inhalt |
|---|---|
| Desktop | KDE Plasma 6 (Wayland), Breeze Dark mit Bibi-Cyan, Biblix-Hintergrund, Bootanimation, Anmeldebildschirm |
| App-Browser | **S-Launcher**: Flathub durchsuchen, Kategorien, App-Seiten mit Screenshots, Installieren/Öffnen/Entfernen, Updates für Apps und System |
| Spiele | **Steam** (Flatpak, inkl. Proton), Steam-Bibliothek im S-Launcher, Big Picture, Lutris/Heroic/Bottles/ProtonUp-Qt per Klick |
| Kernel | **Linux 7.2** aus den offiziellen Debian-Backports, dazu neueste Firmware und Microcode |
| AMD-CPU | amd-pstate (aktiv), Ryzen-Microcode, Kern-Bevorzugung, Temperaturen; abgestimmt auf Ryzen 9000 / 9800X3D |
| AMD-GPU | Mesa 26 mit RADV (Vulkan), Video-Beschleunigung, Firmware, `amdgpu` auch für ältere GCN-Karten, Übertakten mit LACT freigeschaltet |
| NVIDIA | **Treiber 615 fest eingebaut**, direkt von NVIDIA, mit offenen Kernelmodulen (Pflicht für RTX 50 wie die 5070 Ti), Wayland-Modus, Standby-Fix, Flatpak-Treiber für Steam schon im Image |
| HDR | KDE Plasma 6.3 mit HDR unter Wayland, HDR in Spielen über Gamescope (Startoption im S-Launcher) |
| Intel | Mesa + Intel-Media-Treiber |
| Laptops | Hybridgrafik: „Mit dedizierter Grafikkarte starten" im Rechtsklickmenü |
| Leistung | GameMode, **Leistungs-Overlay** im Biblix-Look (Shift rechts + F12 im Spiel), Energieprofil „Leistung" als Standard, zram (komprimierter RAM-Swap), schnelle I/O-Scheduler, Spiele-Kernelwerte wie bei SteamOS, `split_lock` ohne Bremse |
| Alltag | LibreOffice, KDE Connect (Handy), OneDrive, Ersatz-Schriften für Word-Dokumente, RAR/7z, Drucker (HP u. a.) und Scanner |
| Claude | **Claude Desktop** (offizielle Linux-Beta von Anthropic) mit Chat, Cowork und Claude Code |
| Controller | Xbox per Kabel, Bluetooth (xpadneo) und Funkadapter (xone), PS5-Controller, Steam Input, **Sofa-Modus** (S-Launcher und Bibiplexx mit dem Controller bedienen) |
| Zubehör | Eigene Seite im S-Launcher: EasyEffects, GPU Screen Recorder, OBS, OpenRGB, Piper, Solaar, WiVRn (VR), Mission Center, StreamController |
| Sicherheit | Firewall mit Oberfläche (nur KDE Connect, Steam-Streaming, Drucker, VR offen), Timeshift-Snapshots, Secure Boot mit eigenem Schlüssel |
| Updates | Benachrichtigung, wenn System- oder App-Updates da sind; Klick öffnet den S-Launcher. Hinweis, wenn ein Neustart nötig ist (neuer Kernel oder Treiber) |
| Filme & Web | **Bibiplexx** (Filme und Serien, mit TMDB-Postern und Bewertungen) und **Bibi Browser** (Firefox im Biblix-Look) |
| Werkzeuge | **Haustechnik** (Secure Boot, Bildschirme, Platten einrichten), `biblix-gpu` (Grafik-Check), Dolphin-Rechtsklick „Bibi“, fastfetch mit Bibi-Logo, Git, Python, Build-Tools |
| Installer | Calamares, Deutsch (Österreich), Zeitzone Wien |

### Wichtige Befehle

```
s-launcher            App-Browser öffnen
s-launcher --spiele   direkt in den Spielebereich
biblix-gpu            Grafikkarte, Treiber, Vulkan, Secure Boot prüfen
fastfetch             Systeminfo mit Biblix-Logo
```

### Admin-Rechte: `bibi`

Unter Biblix holt man sich Admin-Rechte mit **`bibi`**, nicht mit
`sudo`:

```
bibi apt install htop
bibi biblix-gpu --setup
bibi -i               Admin-Konsole öffnen
```

Die Passwortabfrage zeigt `[bibi] Passwort für …`, beim Tippen
erscheinen Sternchen, Tab-Vervollständigung funktioniert wie gewohnt.
Technisch ist `bibi` das bewährte `sudo` unter Biblix-Namen. `sudo`
selbst bleibt im Hintergrund erhalten, weil Programme und Anleitungen
aus dem Internet es erwarten.

**FPS und Temperaturen im Spiel:** Das Leistungs-Overlay ist in jedem Steam-Spiel schon geladen, aber
versteckt. **Shift rechts + F12** blendet es ein und aus (Biblix Design → Animationen: ausführlich, kompakt
oder aus). Für GameMode im S-Launcher unter Spiele die Startoption `gamemoderun %command%` kopieren.

---

## ISO bauen

Gebaut wird mit Debians `live-build`. Das braucht **Linux** (oder einen
Linux-Container), Root-Rechte, Internet und ca. **25 GB** freien Platz.
Unter Windows geht es direkt nicht, dafür gibt es diese drei Wege:

### Weg A: In der Cloud über GitHub (ohne eigenes Linux) ⭐

1. Den Ordner `biblix/` als eigenes GitHub-Repository hochladen.
2. Auf GitHub: **Actions → „Biblix ISO bauen" → Run workflow**.
3. Nach ca. 1–2 Stunden liegt die ISO unter **Artifacts** zum Download.

### Weg B: Auf einem Debian-13-Rechner

```bash
sudo ./build.sh
```

### Weg C: Mit Docker (z. B. unter Ubuntu, Fedora oder Windows mit WSL + Docker)

```bash
./build-docker.sh
```

Ergebnis: `Biblix-1.0-amd64.iso` plus Prüfsumme. Tipp: Nicht direkt im
OneDrive-Ordner bauen, sondern den Ordner vorher auf eine lokale Platte
kopieren. Das geht schneller und OneDrive synchronisiert keine 20 GB
Bauschutt.

---

## Testen und installieren

**In einer virtuellen Maschine (VirtualBox, VMware, GNOME Boxes):**
EFI aktivieren, 4+ GB RAM, 40 GB Platte, ISO einlegen, starten.
NVIDIA- und Spieleleistung lassen sich in einer VM nicht sinnvoll testen.

**Auf echter Hardware:** ISO mit **Ventoy**, **Rufus** oder
**balenaEtcher** auf einen USB-Stick schreiben, davon starten. Auf dem
Schreibtisch liegen „Biblix installieren", „S-Launcher" und „Spiele".
Live-Benutzer: `bibi`.

### Secure Boot und NVIDIA

Der NVIDIA-Treiber wird lokal gebaut und ist nicht von Microsoft
signiert. Bei aktivem Secure Boot lädt er deshalb nicht. Zwei
Möglichkeiten:

- Secure Boot im BIOS/UEFI ausschalten (einfach), oder
- nach der Installation in der **Haustechnik** (Startmenü) auf „Secure Boot einrichten“
  klicken oder `bibi biblix-secureboot` ausführen: erzeugt einen
  eigenen Schlüssel nur für deinen PC, signiert alle Treiber neu und meldet
  ihn an. Neu starten und auf dem blauen Bildschirm **sofort eine Taste drücken**
  (er wartet nur 10 Sekunden), dann „Enroll MOK“ wählen. Danach Secure Boot im BIOS einschalten. **Nicht** den Schlüssel aus
  `/var/lib/dkms` direkt anmelden: der stammt aus dem ISO-Bau und steckt in
  jeder Kopie der ISO.

`biblix-gpu` zeigt an, ob alles passt.

### Abgestimmt auf: Ryzen 7 9800X3D + RTX 5070 Ti

- **Vor dem ersten Start im BIOS:** Secure Boot aus, EXPO für den
  Arbeitsspeicher an, Bildschirm an die **Grafikkarte** anschließen
  (nicht ans Mainboard).
- **9800X3D:** ein Kernblock mit 3D-Cache, Spiele nutzen ihn
  automatisch. Kein Zusatztreiber nötig. amd-pstate regelt den Takt,
  GameMode schaltet beim Spielen auf volle Leistung.
- **RTX 5070 Ti:** NVIDIA 615 mit offenen Modulen ist fest eingebaut und
  bleibt auf dem 615er-Zweig. Updates kommen über „System aktualisieren"
  im S-Launcher.
- **HDR am Desktop:** Systemeinstellungen → Anzeige → HDR einschalten.
- **HDR in Spielen:** In Steam als Startoption
  `DXVK_HDR=1 gamescope -f --hdr-enabled -- gamemoderun %command%`
  (im S-Launcher unter Spiele → Leistung zum Kopieren).

### Von Windows umsteigen

**Biblix-Befehle für den Anfang:**

```
bibi biblix-secureboot         Secure Boot an lassen (wichtig im Dual-Boot)
bibi biblix-xbox-funkadapter   Xbox-Funkadapter einrichten
biblix-onedrive                OneDrive verbinden (auch im Startmenü)
s-launcher --zubehoer          Ersatz für Hersteller-Software
```

**Installation auf eigene SSDs (empfohlen, Windows bleibt unangetastet):**
1. In Windows unter „Datenträgerverwaltung" notieren, welche zwei SSDs für
   Biblix sind (Modell und Größe). BitLocker-Schlüssel griffbereit halten.
2. In Windows den Schnellstart abschalten (Energieoptionen).
3. Vom USB-Stick starten, „Biblix installieren", bei der Partitionierung
   oben die **richtige SSD auswählen** und „Festplatte löschen". Nur diese
   SSD wird gelöscht. Größe genau prüfen, die anderen bleiben unberührt.
4. Die zweite Biblix-SSD nach der Installation in der KDE-Partitionsverwaltung
   als ext4 formatieren und in Steam als zusätzliche Bibliothek hinzufügen.

**Bootmenü und Wechsel-Knöpfe:**
- Beim Start erscheint das Biblix-Bootmenü: Biblix ist Standard (5 Sekunden),
  Windows steht darunter.
- **In Biblix:** Knopf „Neustart in Windows" auf dem Schreibtisch und im
  Startmenü. Startet einmal direkt Windows, ohne Menü.
- **In Windows:** Auf dem USB-Stick liegt der Ordner `Windows` mit
  „Neustart in Biblix.cmd". Nach `C:\Biblix` kopieren, Verknüpfung auf den
  Desktop legen. Startet einmal direkt Biblix.
- **Windows-Spiele per Knopf:** Auf dem Biblix-Schreibtisch liegt
  „Call of Duty (Windows)". Klick → PC startet in Windows → nach der
  Anmeldung startet Call of Duty von selbst (über Steam, Call of Duty HQ).
  Einmalig in Windows „Spielstarter einrichten.cmd" vom USB-Stick
  doppelklicken. Der Auftrag läuft über den UEFI-Speicher, funktioniert also
  auch mit Windows-Schnellstart und BitLocker. Weitere Spiele: in Biblix
  `/etc/biblix/windows-spiele.conf` und in Windows `C:\Biblix\spiele.ini`
  ergänzen (nur Launcher-Links wie `steam://` sind erlaubt).
- Falls etwas klemmt: Das Bootmenü des PCs (meist F8, F11 oder F12 beim
  Einschalten) zeigt immer beide Systeme.

**Dual-Boot mit Windows:**
- Windows erscheint automatisch im Bootmenü.
- Die Uhr läuft in Ortszeit wie Windows, damit sie nach dem Wechsel stimmt.
- In Windows den **Schnellstart abschalten** (Energieoptionen), sonst sind die
  Windows-Laufwerke gesperrt.
- Spiele unter Biblix nicht auf eine Windows-Platte (NTFS) legen.
- Secure Boot: `bibi biblix-secureboot` erzeugt einen eigenen Schlüssel für
  deinen PC, signiert damit NVIDIA- und Xbox-Treiber neu und meldet ihn beim
  UEFI an. Dann kann Secure Boot an bleiben, das brauchen manche Windows-Spiele.

**WhatsApp:** Eine offizielle WhatsApp-App für Linux gibt es nicht.
Vorinstalliert ist **ZapZap**: WhatsApp Web als eigene App mit
Benachrichtigungen. Einmal per QR-Code mit dem Handy verbinden. Ob Sprach-
und Videoanrufe gehen, hängt davon ab, was WhatsApp Web gerade erlaubt.

**Videos:** **Bibiplexx** ist der Standard-Player (Doppelklick auf ein Video, siehe unten),
mit mpv und Hochqualitäts-Einstellungen (beste Skalierung, Dekodierung über die Grafikkarte,
HDR-Weitergabe, ruckelfreie Bildanpassung). **Haruna** und **VLC** bleiben als Ausweich.

**Zwei Monitore:** Systemeinstellungen → Anzeige. Jeder Monitor mit eigener
Auflösung, Hz-Zahl, Skalierung, VRR und HDR. Den Spiele-Monitor dort als
**Primär** festlegen, dann starten Steam und Spiele auf ihm.

**JBL Quantum:** Läuft als USB-Headset direkt, bei manchen Modellen mit zwei
Ausgängen (Spiel und Chat). Die JBL-Software QuantumENGINE gibt es nicht für
Linux. Equalizer und Mikrofon-Rauschfilter macht **EasyEffects** (Zubehör-Seite).

**VR:** Quest und Pico laufen kabellos über **WiVRn** (App auf der Brille plus
Server auf dem PC). Index und Vive laufen über SteamVR in Steam, mit NVIDIA
aber weniger rund als unter Windows. Meta Quest Link gibt es nicht für Linux.

**Was es unter Linux nicht gibt:** Spiele mit Kernel-Anti-Cheat (Valorant,
Fortnite, aktuelle Call of Duty, Battlefield 6 und andere, siehe
areweanticheatyet.com), Xbox Game Pass zum Installieren, NVIDIA App, RTX HDR,
RTX Video, NVIDIA Broadcast, Adobe-Programme, Microsoft Office als Programm.

### Notfall

Startet der Desktop nicht: Im Bootmenü den Eintrag mit sicherer
Grafik („failsafe" bzw. „recovery mode") wählen und dann `biblix-gpu`
ausführen. Bringt ein Kernel-Update den Treiber durcheinander, bleibt
der vorherige Kernel unter „Erweiterte Optionen" im Bootmenü startbar.

---

## Grenzen (ehrlich)

- **Ältere NVIDIA-Karten:** Die eingebauten offenen Module laufen ab
  GTX 16 / RTX 20. GTX 900 und GTX 1000 (Maxwell, Pascal) werden damit
  **nicht** unterstützt.
- **Reihenfolge beim ersten Mal:** erst die Biblix-Paketquelle auf GitHub
  veröffentlichen, dann die ISO bauen. Sonst findet das fertige System seine
  Update-Quelle nicht.
- **Firewall:** Von außen offen sind nur Handy, Steam-Streaming, Drucker und
  VR. Wer selbst einen Spieleserver betreibt (z. B. Minecraft im Heimnetz),
  gibt den Port in den Systemeinstellungen → Firewall frei.
- **Timeshift** ist installiert, macht aber erst Sicherungen, wenn es einmal
  eingerichtet wurde (Startmenü → Timeshift, Ziel-SSD wählen).
- **Kernel-Update vor NVIDIA:** Kommt ein neuer Kernel, bevor NVIDIA ihn
  unterstützt, startet Biblix mit einfacher Grafik. Im Bootmenü unter
  „Erweiterte Optionen" den vorherigen Kernel wählen, `biblix-gpu` zeigt den Grund.
- **HDR in Spielen** läuft über Gamescope im Vollbild. Plasma 6.3 kann
  HDR, neuere Plasma-Versionen machen es noch runder. Nicht jedes Spiel
  gibt HDR sauber aus.
- Biblix ist auf Ryzen 9800X3D + RTX 5070 Ti abgestimmt, aber nicht
  auf dieser Hardware getestet, solange niemand die ISO darauf
  gestartet hat.
- **Anti-Cheat:** Einige Online-Spiele (z. B. mit Kernel-Anti-Cheat)
  laufen unter Linux grundsätzlich nicht. Vorher auf
  [ProtonDB](https://www.protondb.com) nachsehen.
- Steam ist proprietär. Die Steam-Lizenz bestätigst du selbst beim
  ersten Start.
- `amdgpu.ppfeaturemask` schaltet bei AMD die Übertaktungsregler frei
  (für LACT). Wer das nicht will, entfernt den Eintrag aus
  `/etc/default/grub.d/biblix.cfg` und führt `bibi update-grub` aus.

---

## Biblix Design (ab Design-Update 2.0)

Die App **Biblix Design** (Startmenü → Biblix Design) macht Biblix eigen.
Sie ist ein **Konfigurator**: Dein Desktop ist groß in der Mitte zu sehen,
Leuchtpunkte sitzen auf jedem Teil. Ein Klick auf ein Teil öffnet rechts die
passende Auswahl, unten liegt die Lackfarben-Leiste, „Übernehmen" wendet alles an.

- **Sechs Firmen-Designs**, jeweils dunkel und hell oder automatisch nach
  Tageszeit: Bibi Tech, Bibi Budget Bank, Bibi Delivery, Bibi Mac,
  Nassmacher, Bibiplexx. Dazu **eigene Farben** mischen.
- **Bibi-Startmenü** mit Suche, Schnellknöpfen, angehefteten Apps,
  „Zuletzt gespielt" (inkl. Call of Duty über Windows), CPU-/GPU-Temperatur,
  Bibi-Sprüchen und Schrauben-Knöpfen (Sperren, Standby, Neustart in
  Windows, Neustart, Ausschalten). Auch als Vollbild-Starter.
- **Fensterrahmen** mit Schrauben-Knöpfen (oder Punkte, Terminal, Klammern,
  Kapsel, Balken), nahtlos, farbig oder schlank, runde oder eckige Ecken.
- **Animationen:** Bibi-Pop beim Öffnen, Zusammenziehen beim Schließen,
  Minimieren in die Taskleiste, **3D-Würfel** beim Wechsel der Arbeitsfläche
  (Meta+C dreht ihn per Maus), wackelnde Fenster. Bei Vollbild-Spielen aus.
- **Viele Hintergründe:** elf Motive in deinen Farben, dazu eigene Serien pro
  Firma (z. B. acht Exabibi-Tower-Bilder), auch als Diashow.
- **Lebendige Hintergründe:** 24 animierte Szenen (Sternenflug, Schnee, Leuchtwaben, Synthwave, Prompt mit
  Bibi-Sprüchen, Tower bei Nacht, Donau-Abend, Saallichter …) in deinen Farben bzw. Firmenfarben. Sie pausieren
  automatisch, sobald ein Spiel im Vollbild läuft oder ein Fenster maximiert ist.
- **Symbole und Mauszeiger** in Firmenfarbe, Lade-Zeiger als drehende Mutter.
- **Klänge:** Bibi-Jingle beim Start, Firmen-Klänge (Kassa bei Bibi Mac,
  Roller-Hupe bei Delivery, Kino-Gong bei Bibiplexx …), Retro oder ruhig.
- **Sperrbildschirm** mit großer Uhr und Bibi-Spruch (oder Terminal-Stil),
  Startbildschirm mit dem Schichten-B, **Bootmenü** im Kachel-Stil in
  Designfarbe (fragt dafür einmal nach dem Passwort).
- **Symbole unten rechts** (Lautstärke, Netzwerk, Bluetooth, Benachrichtigungen) im Schrauben-Stil.
- **Arbeitsflächen:** Standard ist eine (kein Umschalter in der Taskleiste), mit „Vier“ gibt es Würfel und Co.
- **Leistungs-Overlay** in Spielen in den Designfarben (ausführlich, kompakt oder aus).
- **Extras:** Terminal-Farben und Biblix-Prompt, Firefox-Startseite, sechs **Firmen-Widgets** für den
  Desktop, Spielereien für die Taskleiste (Spielmodus-Anzeige, Update-Symbol,
  Temperaturen, Kopfhörer-Schalter).
- **Rückgängig** mit Verlauf und **Meine Mischungen** zum Speichern.

Notfall, auch ohne Desktop:

```bash
biblix-design zuruecksetzen
```

Weitere Befehle: `biblix-design presets`, `biblix-design anwenden bibi-mac --hell`.

### S-Launcher-Welten

Der S-Launcher passt sich dem Design an: **Tower** (Bibi Tech, Stockwerke und Aufzugtüren),
**Bestelltheke** (Bibi Mac, Bestellnummer und Abholanzeige), sonst **Schaufenster**. Welt,
Animationen und Klänge stellt man über die Schraubenmutter oben rechts ein. Die Kategorie
**Hausmarke Bibi** zeigt alle Apps, die für Biblix gebaut wurden.

### Flüssig auf 240 Hz (ab biblix-tools 1.3.2 / biblix-system 1.1.0)

- Jeder neue Bildschirm wird einmal automatisch auf die **höchste Bildrate** gestellt (z. B. 240 Hz) und
  Adaptive Sync auf „automatisch“. Danach gilt deine Wahl in den Systemeinstellungen.
  Prüfen: `biblix-bildschirme`, nochmal alle hochstellen: `biblix-bildschirme --jetzt`.
- Spiele: großer NVIDIA-Shader-Cache (weniger Nachladeruckler), DLSS/Reflex in Proton (Steam), Maus und
  Tastatur gehen nie in den USB-Stromsparmodus.
- Flatpak-Apps dürfen Wayland nutzen; Electron-Apps wie Discord laufen nativ (schärfer, volle Bildrate).
- Videos öffnen standardmäßig mit Bibiplexx (Haruna bleibt als Ausweich).

## Bibi Browser

Firefox im Biblix-Look: Leisten, Tabs und Fensterknöpfe in den Farben deines Biblix-Design-Presets,
Bibi-Startseite, uBlock Origin, keine Telemetrie, HTTPS-Modus, Netflix & Co. ohne Rückfrage.
Eigenes Profil (`~/.local/share/bibi-browser`), Standardbrowser von Biblix für Links, Taskleiste und Apps.
Der normale Firefox bleibt daneben. Offene Tabs stellt der Bibi Browser beim nächsten Öffnen selbst wieder her.

## Bibiplexx (Filme und Serien)

**Bibiplexx** sammelt Filme und Serien aus deinen Ordnern (Standard `~/Videos`, weitere in den
Einstellungen) und spielt sie mit mpv im Bibiplexx-Look: Vorhang und Gong beim Start
(Kinomodus), eigene Steuerleiste, Weiterschauen, nächste Folge automatisch, HDR und
Hardware-Dekodierung. Serien werden an `S01E02` oder `1x02` im Dateinamen erkannt.
Dazu: Intro überspringen, „Nächste Folge in …", Schlaf-Timer, Nachtmodus, Untertitel nur bei fremder
Sprache, „Überrasch mich" und ein Rechtsklick-Menü (gesehen markieren usw.).

Im Film: **Bild-Menü** (Taste B: Qualität, Bildglättung, Zoom), **Sprach-Menü** (Taste L: alle Ton- und
Untertitelspuren mit Namen), **Bild-Infos** (Taste I). Unter „Neu dazugekommen“ steht jede Serie einmal.

**Poster und Bewertungen (TMDB):** Mit einem eigenen, kostenlosen Schlüssel von
[themoviedb.org](https://www.themoviedb.org) (Konto → Einstellungen → API) bekommen Filme und Serien echte
Poster und die TMDB-Bewertung (★ 7,9). Die Beschreibung lässt sich zuschalten. Einzutragen unter
Bibiplexx → Einstellungen → „Poster und Bewertungen“. Ohne Schlüssel bleiben die Standbilder aus den Filmen.
*Bibiplexx verwendet die TMDB-API, ist aber nicht von TMDB unterstützt oder zertifiziert.*

Eine **leere** zweite Platte richtet Bibiplexx auf Wunsch als Filmplatte ein
(Einstellungen → „Leere Platte einrichten", Ordner `/media/bibiplexx` mit `Filme/` und `Serien/`).
Platten mit Partitionen oder Daten werden dabei nie angefasst.

## Sofa-Modus (Xbox-Controller)

S-Launcher und Bibiplexx lassen sich komplett mit dem Controller bedienen. Den Auswahlrahmen gibt es erst,
wenn du den Controller benutzt. Mit der Maus sieht alles aus wie immer.

| Taste | S-Launcher / Bibiplexx | Im Film |
|---|---|---|
| Steuerkreuz / linker Stick | Auswahl bewegen | ±10 s spulen, Lautstärke |
| A | Öffnen, Abspielen, Installieren | Pause |
| B | Zurück | Menü zu bzw. Film beenden |
| X | Menü (wie Rechtsklick) | Tonspur wechseln |
| Y | Bibiplexx: „Überrasch mich“ | Untertitel wechseln |
| LB / RB | Bereich wechseln | 1 Minute zurück/vor |
| Start | Vollbild | Pause |

## Haustechnik und Dateimanager

**Haustechnik** (Startmenü, Hausmarke Bibi): Secure Boot mit Anleitung einrichten, alle Bildschirme auf die
höchste Bildrate stellen und **leere Platten einrichten** (als Spiele-, Film- oder Datenplatte; Steam bekommt
automatisch Zugriff).

**Dolphin:** In der Seitenleiste stehen Bibiplexx, Spiele, Daten und OneDrive, sobald es die Ordner gibt.
Rechtsklick → **Bibi**: in Bibiplexx abspielen, als Hintergrund setzen, Bild verkleinern, als JPG/PNG/WebP
speichern, als Admin öffnen, auf eine Windows-Platte kopieren.

---

## Biblix-Updates (eigene Paketquelle)

Biblix besteht aus eigenen Paketen: **`biblix`** (zieht alles mit), `biblix-tools` (S-Launcher, Haustechnik
und Helfer), `biblix-system`, `biblix-design`, `biblix-browser`, `biblix-bibiplexx`, `biblix-xbox` und
`biblix-kwin-wuerfel`.
Jedes Biblix holt neue Versionen aus der Biblix-Paketquelle (GitHub Pages)
und meldet sich mit **„Biblix-Update verfügbar"**. Klick → S-Launcher →
„System aktualisieren". Neu installieren ist nie nötig.

Neue Version veröffentlichen (auf Biblix oder einem anderen Debian 13):

```bash
git clone -b gh-pages https://github.com/Bobbsinator/biblix.git paketquelle
nano pakete/<paket>/VERSION       # Version erhöhen
bash pakete/bauen.sh              # baut nur geänderte Pakete und signiert
bash pakete/veroeffentlichen.sh "Beschreibung"
```

`bauen.sh` baut, signiert die Paketquelle in `paketquelle/` und legt die Pakete auch für den
nächsten ISO-Bau ab. `veroeffentlichen.sh` lädt sie auf GitHub Pages hoch.

Die Pakete sind mit dem Biblix-Schlüssel signiert (Fingerabdruck
`49FC918CBFF609CF881409A1EB1799B26C11B788`). Fremde oder veränderte
Pakete lehnt jedes Biblix ab. Der **private Schlüssel** gehört nur auf den Rechner, der veröffentlicht,
und als Sicherung auf einen USB-Stick. Nicht weitergeben, nicht hochladen. Ohne ihn lassen sich keine
Updates mehr veröffentlichen.

---

## Aufbau

```
biblix/
├── build.sh, build-docker.sh      ISO bauen
├── .github/workflows/             Cloud-Build
├── pakete/                        Biblix-Pakete (je Ordner ein Paket mit VERSION), bauen.sh, veroeffentlichen.sh
├── docs/                          Pläne und Notizen zu den einzelnen Updates
├── auto/config                    live-build-Grundeinstellungen
└── config/
    ├── package-lists/             desktop, gpu, gaming
    ├── hooks/normal/              Build-Schritte im System
    │   ├── 0100 optionale Pakete (MangoHud, gamescope)
    │   ├── 0150 NVIDIA 615 (offene Module) von NVIDIA
    │   ├── 0160 Xbox-Treiber xone + xpadneo
    │   ├── 0170 Claude Desktop
    │   ├── 0200 NVIDIA-Modul bauen und prüfen
    │   ├── 0300 Flathub + Steam, MangoHud, Gamescope, NVIDIA-Flatpak
    │   ├── 0400 Systemname, Dienste, Energieprofil
    │   └── 0500 Logo, Hintergrund, Boot, Login, Installer
    └── includes.chroot/           Dateien, die 1:1 ins System kommen
        ├── usr/share/biblix/s-launcher/s_launcher.py
        ├── usr/bin/biblix-gpu
        ├── usr/lib/sysctl.d, udev, modprobe.d, zram …
        └── usr/share/plymouth/themes/biblix
```

AUF BIBLIX GEHT DAS.
