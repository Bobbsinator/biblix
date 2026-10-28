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

## 1.0.5 (28.10.2026): Firefox nur noch als Bibi Browser

Auf dem PC startete beim Anmelden ein nackter Firefox (systemd-Einheit `app-firefox-esr@…`, also über den
Starter `firefox-esr.desktop`). Statt die Quelle einzeln zu jagen, leitet `biblix-browser` jetzt **jeden** Firefox-Start
um. `postinst` legt per `dpkg-divert` beiseite (`*.biblix-original`) und ersetzt:

- `/usr/share/applications/firefox-esr.desktop` → Starter für `bibi-browser`, versteckt (`NoDisplay=true`).
  Sitzungswiederherstellung, angeheftete Starter und „Öffnen mit Firefox“ öffnen den Bibi Browser.
- `/usr/bin/firefox-esr` und `/usr/bin/firefox` → kleines Skript `exec /usr/bin/bibi-browser "$@"`
  (damit auch `x-www-browser` und das Terminal).

`bibi-browser` ruft deshalb direkt `/usr/lib/firefox-esr/firefox-esr` auf (sonst Endlosschleife). Firefox-Updates
schreiben in die beiseitegelegten Dateien, die Umleitung bleibt. `postrm remove/purge` stellt alles wieder her.
Getestet in einem nachgebauten Mini-System (`DPKG_ROOT`/`DPKG_ADMINDIR`): Einrichten, zweimal Einrichten,
`postrm upgrade` (lässt alles stehen), `postrm remove` (Originale zurück).
Das alte Firefox-Profil unter `~/.mozilla/firefox` bleibt unangetastet; Lesezeichen von dort lassen sich im
Bibi Browser über Lesezeichen → Importieren holen.
