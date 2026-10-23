# Biblix Haustechnik und Neustart-Hinweis (biblix-tools 1.4.0, 23.10.2026)

- **Neustart-Hinweis:** `biblix-neustart-noetig` erkennt neuen Kernel (`/boot/vmlinuz-*` neuer als `uname -r`),
  neuen NVIDIA-Treiber (geladen ≠ installiert) oder `/run/reboot-required`. Meldung mit „Jetzt neu starten“
  (KDE-Neustartdialog) im Update-Check und direkt nach „System aktualisieren“ im S-Launcher.
  Die Update-Meldung nennt Bibiplexx, Bibi Browser und Würfel mit Namen.
- **Haustechnik-App** (`biblix-haustechnik`, Hausmarke Bibi): Übersicht, **Secure Boot** (Einmal-Passwort im Dialog,
  nur der Hash geht per `--hash-datei` an `biblix-secureboot`, Policy `de.biblix.secureboot`; Anleitung für den
  blauen MOK-Bildschirm), **Bildschirme** (`biblix-bildschirme --json`, alle auf höchste Bildrate),
  **Platten** (`/usr/lib/biblix/biblix-platte-einrichten DEV spiele|filme|daten`, nur komplett leere Platten,
  Spieleplatte bekommt Steam-Zugriff per Flatpak-Override).
- **Ruhe und Ordnung:** `/etc/xdg/baloofilerc` (biblix-system 1.2.0) schließt Steam (`~/.var/app`), Spiele, Caches,
  Browser-Profil und Papierkorb von der Dateisuche aus. Der normale Firefox steht nicht mehr doppelt im Startmenü
  (biblix-browser 1.0.1, `applications-merged`). Biblix Design 2.2.0: Extras → „Firmen-Widgets“ → „Auf den Desktop“.
