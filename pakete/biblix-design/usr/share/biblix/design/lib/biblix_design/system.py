"""Systemweite Teile: Bootmenue (GRUB), Startbildschirm (Plymouth), Anmeldung (SDDM).

Laeuft als root ueber den pkexec-Helfer /usr/lib/biblix/biblix-design-system.
Alles wird nach /var/lib/biblix/design/ geschrieben (nicht in Paketdateien).
"""
import subprocess
import tempfile
from pathlib import Path

from .grafik import prompt_b_form, BALKEN
from .kern import mischen, heller, hex_rgb

ZIEL = Path("/var/lib/biblix/design")
PLYMOUTH = Path("/usr/share/plymouth/themes/biblix-aktuell")
GRUB = Path("/boot/grub/themes/biblix-aktuell")
SCHRIFT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SCHRIFT_FETT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SCHRIFT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def _png(svg_text, pfad: Path, w, h):
    with tempfile.NamedTemporaryFile("w", suffix=".svg", delete=False, encoding="utf-8") as f:
        f.write(svg_text)
        quelle = f.name
    try:
        subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h), "-o", str(pfad), quelle], check=True)
    finally:
        Path(quelle).unlink(missing_ok=True)


def _svg(inhalt, w, h, vb=None):
    vb = vb or f"0 0 {w} {h}"
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="{vb}">{inhalt}</svg>'


def _float(h):
    return ", ".join(f"{v / 255:.3f}" for v in hex_rgb(h))


# ---------------------------------------------------------------- Plymouth: Schichten-B baut sich auf

PLYMOUTH_SCRIPT = r"""# Biblix-Startbildschirm: Das Schichten-B baut sich Schicht fuer Schicht auf.
Window.SetBackgroundTopColor(@OBEN@);
Window.SetBackgroundBottomColor(@UNTEN@);
cx = Window.GetX() + Window.GetWidth() / 2;
cy = Window.GetY() + Window.GetHeight() / 2;
k = 1.0;
if (Window.GetHeight() < 900) k = 0.7;

stamm.image = Image("stamm.png");
if (k < 1) stamm.image = stamm.image.Scale(stamm.image.GetWidth() * k, stamm.image.GetHeight() * k);
groesse = 240 * k;
x0 = cx - groesse / 2;
y0 = cy - groesse / 2 - 40;
stamm.sprite = Sprite(stamm.image);
stamm.sprite.SetPosition(x0, y0, 1);

for (i = 0; i < 4; i++) {
    balken[i].image = Image("balken" + i + ".png");
    if (k < 1) balken[i].image = balken[i].image.Scale(balken[i].image.GetWidth() * k, balken[i].image.GetHeight() * k);
    balken[i].sprite = Sprite(balken[i].image);
    balken[i].sprite.SetOpacity(0);
    balken[i].sprite.SetPosition(x0, y0, 2);
}
spruch.image = Image("spruch.png");
if (k < 1) spruch.image = spruch.image.Scale(spruch.image.GetWidth() * k, spruch.image.GetHeight() * k);
spruch.sprite = Sprite(spruch.image);
spruch.sprite.SetPosition(cx - spruch.image.GetWidth() / 2, y0 + groesse + 50 * k, 1);
spruch.sprite.SetOpacity(0);

zeit = 0;
fortschritt = 0;
fun refresh_callback() {
    zeit++;
    # alle Schichten kommen nacheinander von rechts herein; danach im Takt des Fortschritts
    for (i = 0; i < 4; i++) {
        start = i * 14;
        t = (zeit - start) / 18;
        if (t < 0) t = 0;
        if (t > 1) t = 1;
        # sanftes Abbremsen
        e = 1 - (1 - t) * (1 - t) * (1 - t);
        balken[i].sprite.SetOpacity(e);
        balken[i].sprite.SetPosition(x0 + (1 - e) * 160 * k, y0, 2);
    }
    s = (zeit - 70) / 30;
    if (s < 0) s = 0;
    if (s > 1) s = 1;
    spruch.sprite.SetOpacity(s);
}
Plymouth.SetRefreshFunction(refresh_callback);

# --- Passwortabfrage (verschluesselte Platte)
prompt.sprite = Sprite();
dots.sprite = Sprite();
fun display_password_callback(prompt_text, bullets) {
    prompt.sprite.SetImage(Image.Text(prompt_text, @TEXT@));
    prompt.sprite.SetPosition(cx - prompt.sprite.GetImage().GetWidth() / 2, y0 + groesse + 120, 10);
    s = "";
    for (i = 0; i < bullets; i++) s += "* ";
    dots.sprite.SetImage(Image.Text(s, @AKZENT@));
    dots.sprite.SetPosition(cx - dots.sprite.GetImage().GetWidth() / 2, y0 + groesse + 160, 10);
    prompt.sprite.SetOpacity(1);
    dots.sprite.SetOpacity(1);
}
fun display_normal_callback() {
    prompt.sprite.SetOpacity(0);
    dots.sprite.SetOpacity(0);
}
Plymouth.SetDisplayPasswordFunction(display_password_callback);
Plymouth.SetDisplayNormalFunction(display_normal_callback);
msg.sprite = Sprite();
fun message_callback(text) {
    msg.sprite.SetImage(Image.Text(text, @LEISE@));
    msg.sprite.SetPosition(cx - msg.sprite.GetImage().GetWidth() / 2, Window.GetHeight() - 60, 10);
}
Plymouth.SetMessageFunction(message_callback);
"""


def plymouth(p, ziel=PLYMOUTH):
    ziel.mkdir(parents=True, exist_ok=True)
    g = 240
    k = g / 120
    farben = [p["akzent"], heller(p["akzent"], 0.4), p["akzent"], heller(p["akzent"], 0.4)]
    _png(_svg(f'<rect x="{30 * k}" y="{26 * k}" width="{12 * k}" height="{68 * k}" rx="{3 * k}" fill="{p["text"]}"/>', g, g),
         ziel / "stamm.png", g, g)
    for i, (x, y, b) in enumerate(BALKEN):
        _png(_svg(f'<rect x="{x * k}" y="{y * k}" width="{b * k}" height="{12 * k}" rx="{6 * k}" fill="{farben[i]}"/>', g, g),
             ziel / f"balken{i}.png", g, g)
    _png(_svg(f'<text x="360" y="34" text-anchor="middle" font-family="DejaVu Sans Mono" font-weight="bold" '
              f'font-size="26" letter-spacing="3" fill="{p["leise"]}">AUF BIBLIX GEHT DAS.</text>', 720, 48),
         ziel / "spruch.png", 720, 48)
    skript = (PLYMOUTH_SCRIPT.replace("@OBEN@", _float(mischen(p["grund"], p["flaeche"], 0.6)))
              .replace("@UNTEN@", _float(p["grund"])).replace("@TEXT@", _float(p["text"]))
              .replace("@AKZENT@", _float(p["akzent"])).replace("@LEISE@", _float(p["leise"])))
    (ziel / "biblix-aktuell.script").write_text(skript, encoding="utf-8")
    (ziel / "biblix-aktuell.plymouth").write_text(
        "[Plymouth Theme]\nName=Biblix (aktuelles Design)\nDescription=Schichten-B baut sich auf\nModuleName=script\n\n"
        f"[script]\nImageDir={ziel}\nScriptFile={ziel}/biblix-aktuell.script\n", encoding="utf-8")
    return ziel


# ---------------------------------------------------------------- GRUB: Kachel-Bootmenue

GRUB_THEME = """# Biblix-Bootmenue (aktuelles Design) – erzeugt von Biblix Design
title-text: ""
desktop-image: "hintergrund.png"
desktop-color: "@GRUND@"
terminal-font: "DejaVu Sans Mono Bold 16"
terminal-box: "terminal_*.png"

+ image {
    left = 50%-60
    top = 9%
    file = "logo.png"
}
+ label {
    left = 0
    top = 9%+136
    width = 100%
    align = "center"
    font = "DejaVu Sans Bold 24"
    color = "@TEXT@"
    text = "Wohin heute?"
}
+ boot_menu {
    left = 50%-330
    top = 34%
    width = 660
    height = 50%
    item_font = "DejaVu Sans Regular 24"
    item_color = "@TEXT@"
    selected_item_font = "DejaVu Sans Bold 24"
    selected_item_color = "@AUF_AKZENT@"
    icon_width = 48
    icon_height = 48
    item_icon_space = 22
    item_height = 76
    item_padding = 14
    item_spacing = 14
    item_pixmap_style = "kachel_*.png"
    selected_item_pixmap_style = "auswahl_*.png"
    scrollbar = false
}
+ label {
    id = "__timeout__"
    left = 0
    top = 90%
    width = 100%
    align = "center"
    font = "DejaVu Sans Mono Bold 20"
    color = "@AKZENT@"
    text = "Start in %d_"
}
+ label {
    left = 0
    top = 94%
    width = 100%
    align = "center"
    font = "DejaVu Sans Regular 16"
    color = "@LEISE@"
    text = "Pfeiltasten waehlen · Enter startet · E bearbeiten"
}
"""


def _kachel(fuell, rand, pfad_pre: Path, r=16):
    """9-teiliges Pixmap fuer GRUB (Ecken r x r)."""
    teile = {
        "nw": f'<path d="M{r} 0 A{r} {r} 0 0 0 0 {r} V{r} H{r} Z" fill="{fuell}"/><path d="M0 {r} A{r} {r} 0 0 1 {r} 0" fill="none" stroke="{rand}" stroke-width="3"/>',
        "ne": f'<path d="M0 0 A{r} {r} 0 0 1 {r} {r} H0 Z" fill="{fuell}"/><path d="M0 1.5 A{r - 1.5} {r - 1.5} 0 0 1 {r - 1.5} {r}" fill="none" stroke="{rand}" stroke-width="3"/>',
        "sw": f'<path d="M0 0 A{r} {r} 0 0 0 {r} {r} V0 Z" fill="{fuell}"/><path d="M1.5 0 A{r - 1.5} {r - 1.5} 0 0 0 {r} {r - 1.5}" fill="none" stroke="{rand}" stroke-width="3"/>',
        "se": f'<path d="M{r} 0 A{r} {r} 0 0 1 0 {r} V0 Z" fill="{fuell}"/><path d="M{r - 1.5} 0 A{r - 1.5} {r - 1.5} 0 0 1 0 {r - 1.5}" fill="none" stroke="{rand}" stroke-width="3"/>',
        "n": f'<rect width="{r}" height="{r}" fill="{fuell}"/><rect width="{r}" height="3" fill="{rand}"/>',
        "s": f'<rect width="{r}" height="{r}" fill="{fuell}"/><rect y="{r - 3}" width="{r}" height="3" fill="{rand}"/>',
        "w": f'<rect width="{r}" height="{r}" fill="{fuell}"/><rect width="3" height="{r}" fill="{rand}"/>',
        "e": f'<rect width="{r}" height="{r}" fill="{fuell}"/><rect x="{r - 3}" width="3" height="{r}" fill="{rand}"/>',
        "c": f'<rect width="{r}" height="{r}" fill="{fuell}"/>',
    }
    for name, inhalt in teile.items():
        _png(_svg(inhalt, r, r), Path(f"{pfad_pre}{name}.png"), r, r)


def grub(p, hintergrund_svg=None, ziel=GRUB):
    ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "icons").mkdir(exist_ok=True)
    if hintergrund_svg:
        # Hintergrundmotiv abdunkeln, damit die Kacheln lesbar bleiben
        abgedunkelt = hintergrund_svg.replace(
            "</svg>", f'<rect width="100%" height="100%" fill="{p["grund"]}" fill-opacity="0.7"/></svg>')
        _png(abgedunkelt, ziel / "hintergrund.png", 1920, 1080)
    else:
        _png(_svg(f'<rect width="1920" height="1080" fill="{p["grund"]}"/>', 1920, 1080), ziel / "hintergrund.png", 1920, 1080)
    _png(_svg(f'<rect width="120" height="120" rx="26" fill="{p["karte"]}"/>{prompt_b_form(p["text"], p["akzent"])}', 120, 120,
              "0 0 120 120"), ziel / "logo.png", 120, 120)
    _kachel(mischen(p["grund"], p["karte"], 0.8), p["rand"], ziel / "kachel_")
    _kachel(p["akzent"], heller(p["akzent"], 0.35), ziel / "auswahl_")
    _kachel(p["grund"], p["rand"], ziel / "terminal_", 8)
    symbole = {
        "biblix": f'<rect width="120" height="120" rx="26" fill="{p["karte"]}"/>{prompt_b_form(p["text"], p["akzent"])}',
        "windows": f'<rect width="120" height="120" rx="26" fill="{p["karte"]}"/><g fill="{p["text"]}">'
                   '<rect x="28" y="28" width="30" height="30" rx="3"/><rect x="62" y="28" width="30" height="30" rx="3"/>'
                   '<rect x="28" y="62" width="30" height="30" rx="3"/><rect x="62" y="62" width="30" height="30" rx="3"/></g>',
        "system": f'<rect width="120" height="120" rx="26" fill="{p["karte"]}"/>'
                  f'<polygon points="60,22 93,41 93,79 60,98 27,79 27,41" fill="none" stroke="{p["text"]}" stroke-width="8" stroke-linejoin="round"/>'
                  f'<circle cx="60" cy="60" r="14" fill="none" stroke="{p["akzent"]}" stroke-width="8"/>',
    }
    for name, inhalt in symbole.items():
        _png(_svg(inhalt, 120, 120), ziel / "icons" / f"{name}.png", 48, 48)
    for alias in ("debian", "gnu-linux", "gnu", "linux", "os"):
        (ziel / "icons" / f"{alias}.png").write_bytes((ziel / "icons" / "biblix.png").read_bytes())
    for alias in ("windows10", "windows11"):
        (ziel / "icons" / f"{alias}.png").write_bytes((ziel / "icons" / "windows.png").read_bytes())
    for alias in ("efi", "recovery", "memtest"):
        (ziel / "icons" / f"{alias}.png").write_bytes((ziel / "icons" / "system.png").read_bytes())
    for groesse, datei, name in ((16, SCHRIFT, "dejavu_regular_16"), (24, SCHRIFT, "dejavu_regular_24"),
                                 (24, SCHRIFT_FETT, "dejavu_bold_24"), (20, SCHRIFT_MONO, "dejavu_mono_bold_20"),
                                 (16, SCHRIFT_MONO, "dejavu_mono_bold_16")):
        if not (ziel / f"{name}.pf2").exists():
            subprocess.run(["grub-mkfont", "-s", str(groesse), "-o", str(ziel / f"{name}.pf2"), datei], check=True)
    text = (GRUB_THEME.replace("@GRUND@", p["grund"]).replace("@TEXT@", p["text"]).replace("@AKZENT@", p["akzent"])
            .replace("@AUF_AKZENT@", p["auf_akzent"]).replace("@LEISE@", p["leise"]))
    (ziel / "theme.txt").write_text(text, encoding="utf-8")
    return ziel


# ---------------------------------------------------------------- SDDM (Anmeldung): Biblix-Thema (usr/share/sddm/themes/biblix), Hintergrund von hier

def sddm(p, hintergrund_svg=None):
    """Anmeldebildschirm: Breeze-SDDM mit dem Biblix-Hintergrund des aktuellen Designs."""
    d = ZIEL / "sddm"
    d.mkdir(parents=True, exist_ok=True)
    bild = d / "hintergrund.png"
    _png(hintergrund_svg or _svg(f'<rect width="1920" height="1080" fill="{p["grund"]}"/>', 1920, 1080), bild, 1920, 1080)
    return bild
