# Anmeldebildschirm „Biblix“ (biblix-design 2.10.0, 29.10.2026)

Eigenes SDDM-Thema statt Breeze: `pakete/biblix-design/usr/share/sddm/themes/biblix/` (Theme-API 2, Qt 6, nur QtQuick).

- **Aufbau:** Standort-Hintergrund des aktuellen Designs, leicht abgedunkelt; Karte mit blauem B (Biblix-Blau),
  Name (bei mehreren Benutzern mit ‹ › wechselbar), Passwortzeile `passwort>` mit Block-Cursor im Terminal-Stil,
  darunter der Spruch. Falsches Passwort: Karte wackelt, „Das war nicht das Passwort.“; Feststelltaste wird gemeldet.
  Uhr mit Datum oben links auf eigener Tafel (oben rechts tragen die Standort-Bilder oft ihr Typenschild).
  Unten links Sitzung (Klick wechselt), unten rechts Ruhezustand, Neustart, Ausschalten mit Beschriftung.
- **Farben und Hintergrund:** `theme.conf` hat Standardwerte; der Systemhelfer `biblix-design-system` schreibt beim
  Übernehmen (mit „Bootmenü und Startbildschirm mitfärben“) `theme.conf.user` mit Hintergrund und Palette.
  Breeze bekommt weiter seine `theme.conf.user` als Rückfall.
- **Aktiv durch** `/etc/sddm.conf.d/biblix.conf` (`[Theme] Current=biblix`, Conffile). Hat jemand die Datei selbst
  geändert, behält das Update die alte Fassung (`--force-confold`) und es bleibt Breeze.
- **Testen ohne Abmelden:** `sddm-greeter-qt6 --test-mode --theme /usr/share/sddm/themes/biblix`
  (im Testmodus fehlen die Knöpfe zum Ausschalten, weil SDDM dort nichts darf).
- **Hinweis:** Mit automatischer Anmeldung (`/etc/sddm.conf`, `[Autologin]`) erscheint der Bildschirm nur nach dem
  Abmelden oder beim Benutzerwechsel.
