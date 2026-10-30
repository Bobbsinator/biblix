# Biblix-ISO 2.0

Stand 30.10.2026. Plan und Begründungen: `Biblix-ISO-V2/PLAN.md` (OneDrive). Hier steht, was gebaut ist und
wie es zusammenspielt. **Die ISO selbst ist noch nicht gebaut** (Nutzerwunsch: erst später).

## Bauen

```bash
bibi ./build.sh            # Biblix-Pakete aus der veröffentlichten Paketquelle
bibi ./build.sh --lokal    # Biblix-Pakete aus paketquelle/ (noch nicht veröffentlichte testen)
./iso-testen.sh Biblix-2.0-amd64.iso [--secureboot]   # Rauchtest in QEMU mit Fotos
bash pakete/iso-signieren.sh Biblix-2.0-amd64.iso     # Prüfsumme signieren (lokal, privater Schlüssel)
```

- **Version an einer Stelle:** `iso.conf` (`ISO_VERSION="2.0"`). `build.sh` schreibt sie nach
  `/etc/biblix-iso` im Image; Hooks 0400/0500 lesen sie (Anmeldetexte, Installer-Branding),
  `auto/config` für die ISO-Kennung. os-release kommt aus biblix-system (jetzt „Biblix 2.0“).
- **Pakete:** `build.sh` lädt `InRelease`, prüft die Signatur mit `pakete/biblix-archive-keyring.gpg`,
  prüft den Hash der Paketliste und holt für jedes Paket aus `pakete/` die neueste Version (egal ob `all`
  oder `amd64`, damit ist der Würfel-Fehler H3 weg), jeweils mit Prüfsumme. `config/packages.chroot/*.deb`
  steht jetzt in `.gitignore`: **keine „ISO-Paket“-Commits mehr**.
- **Vorabprüfung:** Platz (25 GB), Werkzeuge, Syntax aller Hooks.
- **squashfs mit zstd** (`auto/config`): startet schneller als xz.
- **GitHub Actions** (`.github/workflows/build-iso.yml`): von Hand oder per Tag `v2.0`. Bei einem Tag ein
  GitHub-Release; über 2 GB wird die ISO in Teile zerlegt (`ZUSAMMENSETZEN.txt` erklärt das Zusammenfügen).

## Zeitmaschine (Btrfs + Snapper)

- Installer: `config/includes.chroot/etc/calamares/modules/partition.conf` (Btrfs Standard, ext4 wählbar,
  Swap-Datei) und `mount.conf` (Unterteile `@`, `@home`, `@cache`, `@log`, `@swap`; `noatime,compress=zstd:1`).
- Paketliste `zeitmaschine.list.chroot`: btrfs-progs, snapper, btrfs-assistant.
- Erster Start: `biblix-erststart` richtet Snapper für `/` ein (keine stündlichen Schnappschüsse, Liste für
  die Gruppe sudo lesbar). Danach macht der apt-Hook von snapper (`/etc/apt/apt.conf.d/80snapper`) vor und
  nach jedem Update ein Paar.
- Haustechnik → **Zeitmaschine** (nur sichtbar, wenn Snapper eingerichtet ist): Updates als Paare,
  „Zurückdrehen“ (`snapper undochange`, vorher eigener Schnappschuss), „Jetzt Schnappschuss machen“,
  Btrfs Assistant. Root-Teil: `/usr/lib/biblix/biblix-zeitmaschine` über polkit `de.biblix.zeitmaschine`.
- `/home` liegt in `@home` und wird nie zurückgedreht. Booten in alte Stände (grub-btrfs) gibt es in
  Debian 13 nicht; das wäre ein eigenes Paket für später.

## Secure Boot ab Werk

- Hook 9100 löscht den DKMS-Schlüssel aus dem ISO-Bau (vorher steckte derselbe private Schlüssel in jeder
  Kopie).
- `biblix-erststart` ruft `biblix-secureboot --nur-schluessel`: eigener Schlüssel, alle Treiber neu signiert
  (transaktional), ohne UEFI-Anmeldung. Die bietet der Willkommens-Assistent → Haustechnik an.
- Der Dienst `biblix-erststart.service` läuft nur mit `/etc/biblix-iso`, nicht im Live-System
  (`boot=live`) und nur einmal (`/var/lib/biblix/erststart-erledigt`). Bestehende Biblix-PCs sind nicht
  betroffen. Er hält die Anmeldung nicht auf.

## Willkommen bei Biblix

`biblix-willkommen` (biblix-tools 1.8.0, `usr/share/biblix/willkommen/willkommen.py`), im Haustechnik-Look:

1. Willkommen · 2. Design (Presets als Musterkarten, hell/dunkel/auto, `biblix-design anwenden`) ·
3. Bildschirme (`biblix-bildschirme`) · 4. Sicherheit (Secure Boot → Haustechnik, Zeitmaschine) ·
5. Spiele (S-Launcher, Spieleplatten) · 6. Konten (OneDrive, Claude, S-Launcher) · 7. Fertig.

Alles überspringbar. Autostart (`--autostart`) nur auf Systemen aus der ISO 2.0+ und nur einmal
(`~/.config/biblix/willkommen.json`). Im Live-System stattdessen „Ausprobieren oder installieren“ mit
Hinweis auf Windows-Schnellstart und BitLocker. Im Startmenü und in der Hausmarke Bibi jederzeit erreichbar.
Feinschliff am Aussehen: gern mit dem Design-Chat.

## Installer

- Diashow `config/includes.chroot/usr/share/biblix/branding/calamares/show.qml` (sechs Karten im
  Bibi-Tech-Look, nur QtQuick), Hook 0500 kopiert sie ins Branding und setzt die Seitenleiste in Biblix-Farben.
- ISO-Bootmenü (schon vorher): Biblix starten, sichere Grafik, Stick prüfen, UEFI-Einstellungen.

## Gelernt beim ersten Bau (30.10.2026)

- Bau in WSL (`/root/biblix-iso`, Kopie des Repos) dauert rund 20 Minuten, ISO 5,9 GB.
- **Nie `lb clean --binary` allein aufrufen:** `auto/clean` löscht dabei die Konfiguration, live-build fällt
  auf Debian *testing* zurück und verdirbt das Chroot. Immer komplett über `build.sh`.
- Bauordner nur löschen, wenn nichts mehr darin eingehängt ist, und mit `rm -rf --one-file-system`.
- **Secure Boot:** Das signierte GRUB darf unter Secure Boot keine Zusatzmodule nachladen
  („prohibited by secure boot policy“); das grafische ISO-Menü blieb leer und startete nicht.
  `config/bootloaders/grub-pc/config.cfg` nimmt deshalb bei `lockdown=y` das schlichte Textmenü.
- QEMU mit Secure-Boot-Firmware stürzt unter WSL-KVM manchmal im SMM ab; dann ohne KVM testen.

## Noch offen

- ISO bauen, `iso-testen.sh` (mit und ohne Secure Boot), Installation in der VM, dann am echten PC.
- Würfel neu bauen geht mit `pakete/baukiste-einrichten.sh` (Baukiste war am 23.10. weg, Skript ist da).
- grub-btrfs als eigenes Paket (Booten in alte Stände), wenn gewünscht.
