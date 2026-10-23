# Bibi Browser (biblix-browser 1.0.0)

Entscheidung vom 23.10.2026: **Variante A** – Firefox ESR mit eigenem Profil und Biblix-Look
(nicht eigene Engine: Streaming mit Widevine, Erweiterungen und Sicherheitsupdates von Debian bleiben).
Name „Bibi Browser“ (Biblix-Produktname, kein Lore-Kanon), Standardbrowser über `/etc/xdg/mimeapps.list`
(biblix-system 1.1.1) und `InitialPreference`.

- `bibi-browser` (Python) erzeugt bei jedem Start aus `~/.config/biblix/palette.json`:
  `userChrome.css` (Leisten, Tabs, Prompt-B-Logo, Adressleiste, Schrauben-Fensterknöpfe, drehende Mutter beim Laden),
  `userContent.css` („Neuer Tab“ im Bibi-Look) und die Bibi-Startseite. Grundeinstellungen (Startseite, keine
  Telemetrie/Pocket/Sponsoren, HTTPS-Modus, GPC, Widevine, Mittelklick-Scrollen, KDE-Dateidialog) setzt `user.js`
  nur **einmal** (Merker `bibi-einstellungen.json`); danach gelten die Änderungen des Nutzers. Pflicht ist nur
  `toolkit.legacyUserProfileCustomizations.stylesheets`. Läuft der Browser schon, wird nichts an Einstellungen geschrieben.
  Profil: `~/.local/share/bibi-browser/profil` (Lesezeichen usw. bleiben). Eigene CSS: `chrome/userChrome-eigen.css`.
- uBlock Origin wird beim Paketbau von addons.mozilla.org geholt, beim ersten Start ins Profil gelegt;
  Firefox prüft die Mozilla-Signatur und aktualisiert es selbst.
- Startet Firefox mit `--name/--class bibi-browser` (eigenes Fenster-/Taskleistensymbol, getrennt vom normalen Firefox).

Getestet im Chroot (mit D-Bus): eigene Änderungen überleben den Neustart, zweiter Start/Link öffnet einen Tab
im laufenden Fenster, Startmenü-Eintrag und Symbol gültig. Außerdem mit echtem Firefox ESR unter Xvfb (Bibi Tech dunkel, Bibi Mac hell): Startseite, Neuer Tab,
uBlock aktiv und signiert. Nicht getestet: Schrauben-Fensterknöpfe unter KDE/Wayland (CSD), Netflix.
