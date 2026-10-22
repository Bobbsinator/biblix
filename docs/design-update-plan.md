# Biblix Design-Update – Planung

Ziel des Nutzers: **Biblix soll richtig eigen und besonders aussehen** („richtig Bibi").
Vorgehen: erst alles Schritt für Schritt planen, dann **ein komplettes Design-Update** bauen
und über die Paketquelle verteilen (keine Neuinstallation).

## Grundidee

- **Design-App** mit zwei Bereichen:
  - **Presets:** fertige Komplett-Looks mit einem Klick (je eine Bibi-Firma).
  - **Mischen:** jeden Baustein einzeln wählen, eigene Mischung als Preset speichern.
- Neue Designs, Animationen und Startmenüs kommen später als Updates dazu.
- Schalter „Animationen aus"; Spiele im Vollbild sind davon nicht betroffen.
- **Wunsch des Nutzers: Die Design-App bekommt wirklich viele Optionen, und das Mischen ist das Highlight.**
  Jede nicht gewählte Variante aus der Planung wird dort eine Option.

## Bausteine und Planungsstand

| Nr. | Baustein | Stand |
|---|---|---|
| 0 | **Biblix-Logo (neu)** | **Gewählt: A „Prompt-B"** (`>` + B + blauer Cursor) als Hauptlogo/Startknopf. Startbildschirm (Plymouth/Ladeanimation): **Schichten-B baut sich Schicht für Schicht auf**, darunter „AUF BIBLIX GEHT DAS.". Standard-Hintergrund: **großes Schrauben-B als Bauplan-Zeichnung**. Weitere Varianten später in der Design-App. Firmenlogos je Design. |
| 1 | Startmenü | **Gewählt: A, komplett eigenes Bibi-Startmenü** (eigenes Plasma-Widget in QML). Aufbau laut Entwurf + CPU-/GPU-Temperatur + Bibi-Spruch. Öffnen: „Bibi-Pop" (gleitet von unten, federt nach). Startknopf: neues Biblix-Logo, umstellbar auf Firmenlogo. Position (links/mittig) einstellbar. |
| 2 | Taskleiste | **Standard:** schwebend mit runden Ecken (legt sich bei maximiertem Fenster an den Rand), **undurchsichtig** (seit 2.0.1, Wunsch des Nutzers; Milchglas wählbar), auf beiden Monitoren (jeder nur eigene Fenster, Uhr/Symbole nur Hauptmonitor). Keine Extras im Standard. **Design-App:** fest/Dock, undurchsichtig/adaptiv, Monitor-Varianten und Spielereien (Spielmodus-Anzeige, Update-Symbol, CPU/GPU-Mini-Anzeige, Kopfhörer-Schalter) als Optionen. |
| 3 | Animationen | **Standard:** Öffnen „Bibi-Pop" (wächst aus der Mitte, federt nach), Schließen zusammenziehen + verblassen, Minimieren in die Taskleiste fliegen, Arbeitsfläche wechseln **3D-Würfel**, **wackelnde Fenster** an. Pause bei Vollbild-Spielen, alles abschaltbar. Technik: eigene KWin-Effekte; Würfel gibt es in Plasma 6 nicht mehr eingebaut → Community-Effekt `kwin-effects-cube` selbst als Paket bauen (passend zu KWin 6.3). **Design-App:** alle anderen Varianten (Hochgleiten, Aufbauen/Abbauen, Wegfallen, Wabern, Gleiten, Überblenden, Durchsichtig beim Verschieben, Klick-Funken) als Optionen. |
| 4 | Fensterrahmen | **Standard:** nahtlose Titelleiste (gleiche Farbe wie Fenster, aktives Fenster mit dünner Akzentlinie oben), Knöpfe rechts, abgerundete Ecken, leichter Schatten (aktives Fenster stärker). **Knopf-Stil: Schrauben-Knöpfe** (Sechskant-Muttern): Symbol immer sichtbar, ausgegraut; beim Drüberfahren füllt sich die Mutter mit Farbe (Akzent, Schließen rot) und dreht sich eine Sechsteldrehung. Inaktive Fenster noch blasser. **Design-App:** farbige/schlanke Titelleiste, Knöpfe links, eckig. |
| 5 | Farben und Presets je Bibi-Firma | In Arbeit. Festgelegt: **Bibi Budget Bank** = dunkelgrün + braun mit Goldakzenten; **Bibi Delivery** = gelb + knalliges Blau (kräftiger als das Biblix-Blau). Lore-Abgleich (Masterbrief): Bibi Tech = Navy/Graphit/Schwarz/Electric Blue + Gelb als B-Akzent; Bibi Mac rot-gelb; Bibiplexx Kino/dunkel; Nassmacher bunt/sommerlich; BBB seriös (Website-Darstellung, kein harter Kanon). **Liste bestätigt: die 6 Presets wie im Farbentwurf** (Bibi Tech mit gelbem B-Akzent, BBB, Delivery, Mac, Nassmacher bunt mit Cyan-Basis, Bibiplexx). **Design-App: eigene Farben frei mischen** (Hintergrund, Fläche, Akzent, Zweitakzent, Text). Helle Varianten: vorläufig A (jedes Preset auch hell, umschaltbar/automatisch), Nutzer kann noch ändern. Hinweis: Das sind Biblix-Designs, keine neuen Lore-Festlegungen zu Firmenfarben. |
| 6 | Icons und Mauszeiger | **Standard:** eigene Biblix-Symbole für das Wichtigste (S-Launcher, Design-App, Dateien, Ordner, Terminal, Einstellungen, Papierkorb, Biblix-Werkzeuge), Rest aus fertigem Set in Akzentfarbe eingefärbt; Ordner färben sich mit dem Preset. Stil: rund-eckige Kacheln. Mauszeiger: eigener Biblix-Pfeil in Akzentfarbe mit dunklem Rand, Lade-Zeiger = drehende Sechskant-Mutter. **Design-App:** flache/Linien-Symbole, Lade-Zeiger Terminal-Cursor oder Schichten-B, normale Zeiger. |
| 7 | Anmelde-/Sperrbildschirm und Ladeanimation | **Standard:** großer Bibi-Sperrbildschirm (Uhr + Datum groß, Bibi-Spruch, Benutzerbild, Passwortfeld in Milchglas, Schrauben-B-Hintergrund des Presets, Schrauben-Knöpfe Ausschalten/Neustart/Neustart in Windows) – gleicher Look für SDDM-Anmeldung und KDE-Sperrbildschirm. Ladeanimation nach Login: Prompt-B tippt „AUF BIBLIX GEHT DAS.", dann Desktop-Pop. **Automatische Anmeldung bleibt** (Nutzer-PC springt direkt zum Desktop); Sperrbildschirm erscheint beim Sperren/Standby. Hinweis: Bei Auto-Login öffnet sich KWallet nicht automatisch → ggf. Wallet ohne Passwort einrichten. **Design-App:** Terminal-Anmeldung, schlicht; Ladeanimation Schrauben-B oder Einblenden. |
| 8 | Systemklänge | **Standard:** Biblix-Technik-Klänge (kurz, sauber, leicht mechanisch: Anmelden = aufsteigender Dreiklang + Einrast-Klick, Hinweis = weiches Pling, Fehler = dumpfes Klonk). **Startklang: cooler Bibi-Jingle** beim Desktop-Pop (kurz, nicht zu laut). **Preset-Akzentklänge** (nur Start + Hinweis): BBB Münzklimpern, Delivery Motorroller-Hupe (Lore: Delivery fährt Motorroller), Bibiplexx Kino-Gong, Nassmacher Plätschern, Bibi Mac und Bibi Tech noch festlegen. Klänge per Synthese selbst erzeugt (keine Urheberrechtsprobleme). **Design-App:** Retro-Terminal, ruhig, Startklang aus. |
| 9 | Bootmenü und Bootlogo | **Färben sich automatisch mit dem Preset** (GRUB-Theme + Plymouth Schichten-B in Preset-Farben; einziger Schritt mit `bibi`-Rechten über polkit, Passwortabfrage beim Wechsel). **Neuer Stil:** Prompt-B oben, Einträge als Kacheln mit Symbolen (Biblix, Windows, UEFI), Zähler im Terminal-Stil „Start in 5_". |
| 10 | Die Design-App selbst | Name: **Biblix Design**. Bereiche: Presets, Mischen, Farben, Spielereien, Meine Mischungen, Neue Designs. Extra: **Rückgängig + Verlauf**. Kein Spruch beim Übernehmen. **Aufbau: Konfigurator** – eigener Desktop groß in der Mitte, Leuchtpunkte auf jedem Teil, Klick auf das Teil öffnet die Auswahl direkt dort, Farben als Lackfarben-Leiste unten. Muss **ordentlich und aufgeräumt** sein (klare Abstände, eine Auswahl gleichzeitig offen, gut lesbar). **Neu: Hintergrundbilder** – Klick auf den Desktop-Hintergrund: Schrauben-B-Bauplan in Preset-Farben, Firmenlogo-Hintergründe, eigene Bilder, Diashow. Firmenlogos liefert der Nutzer als Grundlage. |

## Technische Umsetzung (geplant)

- Alles als Debian-Pakete über die Paketquelle (biblix-design wird erweitert, evtl. eigenes Paket pro Firmen-Design).
- Startmenü: Plasma-6-Widget (QML), ersetzt Kickoff in der Taskleiste.
- Animationen: eigene KWin-Effekte.
- Umschalten aus der App: `plasma-apply-colorscheme`, `plasma-apply-desktoptheme`, `plasma-apply-lookandfeel`,
  `kwriteconfig6`, KWin per D-Bus. Läuft als normaler Benutzer, kein `bibi` nötig
  (außer für Bootmenü/Bootlogo, die systemweit gelten).

## Bauplan (Reihenfolge)

1. Grundlagen: Biblix-Logo (Prompt-B), Firmenlogos, Farbpaletten (6 Presets × dunkel/hell) als Quelldateien.
2. Plasma-Teile: Farbschemata, Plasma-Stil (Taskleiste Milchglas, schwebend), Fensterrahmen mit Schrauben-Knöpfen, Icons, Mauszeiger.
3. Bibi-Startmenü (QML-Widget) inkl. Temperaturen, Sprüche, Bibi-Pop.
4. KWin-Effekte: Bibi-Pop, Zusammenziehen, Minimieren, Würfel (Paket), wackelnde Fenster; Pause bei Vollbild.
5. Sperr-/Anmeldebildschirm, Ladeanimation (Prompt-B tippt), Plymouth (Schichten-B), GRUB (Kachel-Stil) – je Preset.
6. Klänge (Synthese) inkl. Bibi-Jingle und Preset-Akzente.
7. Hintergründe: Schrauben-B-Bauplan je Preset, Tower-Serie, eigene Motive je Firma.
8. App „Biblix Design" (Konfigurator) + Rückgängig/Verlauf + **Notfall-Zurücksetzen** auf Biblix-Standard.
9. Test in der VM, dann Freigabe durch Nutzer, dann Veröffentlichung über die Paketquelle.

## Umsetzung (Stand 2026-10-21)

Gebaut, noch **nicht veröffentlicht** (wartet auf Freigabe):

| Paket | Version | Inhalt |
|---|---|---|
| biblix-design | 2.0.0 | Generatoren (Farbschema, Aurorae-Rahmen, Zeiger, Symbole, Terminal, Hintergründe, Plymouth, GRUB, SDDM), App „Biblix Design", Bibi-Startmenü + 4 Spielereien-Widgets, KWin-Effekte (biblix_fenster, biblix_minimieren), Sperrbildschirm-Anpasser, Klänge, Sprüche, Firefox-Startseite |
| biblix-kwin-wuerfel | 1.0.0 (amd64) | 3D-Würfel, portiert von kwin-effects-cube für KWin 6.3, dreht beim Arbeitsflächenwechsel |
| biblix-tools | 1.2.0 | S-Launcher folgt den Designfarben |
| biblix | 1.1.0 | Sammelpaket zieht Design 2.0 und Würfel |

Technik-Entscheidungen:
- Alles wird aus der Palette **erzeugt** (auch eigene Farben): Themen landen im Benutzerordner (A/B-Namen, damit Plasma neu lädt).
- Bootmenü/Startbildschirm/Anmeldung: pkexec-Helfer `/usr/lib/biblix/biblix-design-system`, Ausgabe nach `/boot/grub/themes/biblix-aktuell`, `/usr/share/plymouth/themes/biblix-aktuell`, `/var/lib/biblix/design`.
- Sperrbildschirm: KDE-Datei per dpkg-divert, Biblix-Fassung wird aus dem Original erzeugt; passt die Plasma-Version nicht, bleibt KDE-Original.
- Anmeldebildschirm (SDDM): Breeze mit Biblix-Hintergrund (Auto-Login, selten sichtbar).
- Sperrbildschirm ohne Ausschalten-Knöpfe (KDE erlaubt das aus Sicherheitsgründen nicht ohne Entsperren).

## Entscheidungen

- 2026-10-21: Design-Update wird erst komplett geplant, dann gebaut.
- 2026-10-21: Startmenü Variante A (komplett eigen). Alle vorgeschlagenen Bausteine kommen rein.
- 2026-10-21: Startmenü-Details: CPU-/GPU-Temperatur, Spruch-Feld, Öffnen-Animation A („Bibi-Pop"),
  Startknopf = neues Biblix-Logo (Firmenlogo wählbar), Position einstellbar.

## Firmenlogos (nur Richtungsvorgabe)

- Gewählt: **BBB 1** (Siegel mit BBB-Monogramm), **Bibi Mac 2b** (Schriftzug bibi/mac, knallrot, hellgelb + weiß),
  **Bibi Tech C** (Typenschild im Messrahmen, ohne graue Zeile, gelber Knopf als Ecke oben rechts),
  **Delivery 3c** (Kapsel-Schriftzug, komplett in Blau, richtiger Pfeil), **Nassmacher B** (zwei Rutschen starten gemeinsam),
  **Bibiplexx C + A** (Leinwand-Rahmen mit Pixel-Elementen). Delivery 3c (blau, echter Pfeil) **fertig**. Tech C **fertig** (Variante gelbes Eck-Quadrat oben rechts). Plexx **fertig: Plexx 1** („plexx" komplett aus Pixeln, saubere X, gerade Sitzreihe, mittlerer Platz leuchtet orange).
- Akzentklänge fertig: Bibi Mac = **Kassa-Sounds** (Kassenlade/Bon-Drucker-Klingeln), Bibi Tech = Hochfahr-Summen mit kurzem Daten-Zirpen.
- Tower-Hintergründe: Wien bei Nacht, Bauplan (444 m, 94 OG), Froschperspektive, Morgennebel über der Donau; optional Gewitter, Blick von oben. Auch als Diashow.
- **Bibi Tech bekommt mehrere Exabibi-Tower-Hintergründe** (Wunsch: sollen zu den coolsten gehören).
- **Wichtig:** Die Logos sind **nur Stil-Vorgabe**, nicht überall drauf. Hintergrundbilder und andere Teile sind
  **eigene Motive im Stil der Firma**, nicht das Logo in groß.
- Biblix-Designs, keine Lore-Festlegung.

## Bibi-Sprüche (für Startmenü)

- Liste ikonischer Sprüche aus der vorhandenen Lore sammeln (Masterbrief, Entscheidungslog), Nutzer wählt aus.
- Neue Sprüche nur mit Zustimmung des Nutzers (kein heimlicher Kanon).
- Liste als eigene Datei im Paket, damit neue Sprüche per Update kommen.

## Später (eigene Updates, nicht Teil des Design-Updates)

- **Bibiplexx-App:** eigener Video-/Filmplayer im Bibiplexx-Stil. **Gewählt: A**, eigene App auf mpv-Basis
  (libmpv, HDR, NVIDIA-Decoding) mit eigener Oberfläche (Filmsammlung, Kinomodus, „Reihe sieben"). Lore-Regel beachten:
  kein süßes Popcorn, nicht einmal als UI-Option. **Gebaut am 22.10.2026 als biblix-bibiplexx 1.0.0**, siehe `docs/bibiplexx.md`.
