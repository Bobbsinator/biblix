# Sicherheitsnetz und Sicherheit (Prüfbericht Phase 1, Pakete A und B)

Stand 25.10.2026: biblix-tools 1.6.0, biblix-system 1.4.0, biblix-design 2.4.1, biblix-browser 1.0.4.
Grundlage: `Biblix-Pruefung/PRUEFBERICHT-PHASE1.md` (unabhängiger Prüf-Chat).

## A · Sicherheitsnetz

**H1 · Abgebrochenes Update repariert sich selbst.** `/usr/lib/biblix/biblix-system-update` führt vor jedem
Update `dpkg --configure -a` und `apt-get -f install` aus. Klappt die Reparatur nicht, steht im Protokoll,
was im Terminal zu tun ist.

**H2 · Schließen des S-Launchers bricht nichts mehr ab.** Das Update läuft als eigener Systemdienst
(`systemd-run --unit=biblix-system-update`), Protokoll in `/var/log/biblix/system-update.log`, Ergebnis in
`/run/biblix/system-update.ergebnis`. Der S-Launcher schaut nur zu. Ein zweiter Klick zeigt das laufende
Update, statt ein zweites zu starten. Beim Schließen fragt der S-Launcher nach, solange ein Auftrag läuft.
Ohne systemd (Installer-Chroot) läuft das Update direkt.

**H6 · Neuer Kernel ohne NVIDIA-Treiber.** `/usr/lib/biblix/biblix-kernel-grafik`, aufgerufen von
`/etc/kernel/postinst.d/zz-biblix-grafik` (nach dkms), `/etc/kernel/header_postinst.d/zz-biblix-grafik` und am
Ende jedes System-Updates. Hat der neueste Kernel kein `nvidia.ko`, der laufende aber schon, wird der laufende
Kernel per `grub-set-default` Standard (dafür jetzt `GRUB_DEFAULT=saved` in `biblix.cfg`). Merker:
`/var/lib/biblix/kernel-zurueckgehalten`. Sobald das Modul da ist, wird der neue Kernel freigegeben
(`grub-set-default 0`). Der Neustart-Hinweis ignoriert einen zurückgehaltenen Kernel, `biblix-update-check`
meldet ihn einmal. Zustand: `biblix-kernel-grafik --zustand`. Ohne NVIDIA passiert nichts.

**M4 · Fehler werden sichtbar.** `update-initramfs` und `update-grub` in den postinst/postrm-Skripten und in
`biblix-design-system` melden Fehler jetzt im Update-Protokoll (letzte 5 Zeilen) und im Journal
(`journalctl -t biblix`). Das Paket bleibt trotzdem installierbar.

## B · Sicherheit

**H4 · Kein Mitlesen von Tastaturen über hidraw.** `70-biblix-zubehoer.rules` gibt HID-Rohzugriff weiter für
OpenRGB, Piper, Solaar, Headsets und Controller, aber nicht mehr für Geräte mit Tastatur:
`/usr/lib/biblix/biblix-hid-pruefen` prüft, ob ein Eingabegerät desselben HID-Geräts die Tasten Q, A und Z kennt.
Schon vergebene Rechte gelten bis zum nächsten Neustart. Prüfen: `getfacl /dev/hidraw*`.
Hinweis: Eine Gaming-Maus mit Makro-Tastatur-Teil hat für genau diesen Teil keinen Rohzugriff mehr; ihr
RGB-/Einstellungs-Teil ist meist ein eigenes hidraw und geht weiter.

**H5 · Secure Boot einrichten ist jetzt „alles oder nichts“.** `biblix-secureboot` sichert vorher den alten
Schlüssel und alle eingebauten DKMS-Module (`/var/lib/biblix/mok-sicherung`). Kernel ohne Header werden
übersprungen (mit Hinweis). Schlägt ein Modul fehl, kommen Module und Schlüssel zurück, der Merker wird nicht
gesetzt. Gibt es für keinen Kernel Header, bricht es vor jeder Änderung ab.

**M1 · Firefox-Medien-Sandbox nur im Bibi Browser gelockert.** `MOZ_DISABLE_RDD_SANDBOX=1` (für die
NVIDIA-Videodekodierung) setzt nur noch `bibi-browser`, nicht mehr `/etc/profile.d` für jedes Programm.

**M2 · Keine still eingeschalteten fremden Erweiterungen.** `extensions.autoDisableScopes` ist jetzt Pflichtwert
14: Nur Erweiterungen im eigenen Profil (uBlock Origin) starten ohne Rückfrage. Was andere Programme für alle
Nutzer oder systemweit ablegen, muss man selbst freigeben. Gilt auch für bestehende Profile.

## Getestet (Test-Chroot und WSL)

- Installation aller vier Pakete, Hooks ausführbar, `GRUB_DEFAULT=saved`.
- H1: entpacktes, nicht eingerichtetes Paket wird vom Update fertig eingerichtet, `dpkg --audit` danach leer.
- H2: Dienst-Weg auf WSL mit Ersatz-Update: Protokoll läuft mit, Ergebniscode kommt an, Abbruch des Zuschauers
  lässt den Dienst weiterlaufen, kein übriger Prozess.
- H6: zurückhalten, Neustart-Hinweis still, Freigabe nach Modulbau, ohne NVIDIA keine Änderung.
- H4: Tastatur → kein Zugriff, Maus und Headset → Zugriff; `udevadm verify` ohne Fehler.
- H5: Fehler beim zweiten Modul → alte Module und alter Schlüssel zurück; ohne Fehler → neue Module, Merker gesetzt.
- M1/M2: user.js mit `autoDisableScopes 14` bei jedem Start; systemweit kein `MOZ_DISABLE_RDD_SANDBOX` mehr.

**Nicht testbar ohne echten PC:** echtes DKMS mit NVIDIA, echte HID-Geräte, Plasma-Dialog beim Schließen,
GRUB mit `saved` beim echten Start.
