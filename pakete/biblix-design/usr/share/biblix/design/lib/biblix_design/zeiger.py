"""Mauszeiger im Biblix-Stil (XCursor), gerendert mit rsvg-convert und xcursorgen."""
import shutil
import subprocess
import tempfile
from pathlib import Path

from .grafik import SECHSECK

GROESSEN = [24, 32, 48, 64]
UMRISS = "#0b0d12"

PFEIL = "M4 2 L4 24 L9.5 18.8 L13.2 27.2 L17 25.5 L13.4 17.3 L21 17.3 Z"
HAND = ("M12 3.5c-1.4 0-2.4 1-2.4 2.4V16l-1.9-1.9c-1-1-2.5-1-3.4-.1-.9.9-.9 2.3 0 3.3l6.2 7"
        "c1.3 1.5 3.1 2.2 5 2.2h3.2c3.3 0 6-2.7 6-6v-6.3c0-1.3-1-2.3-2.3-2.3-.5 0-.9.1-1.3.4"
        "-.3-1-1.2-1.6-2.2-1.6-.6 0-1.1.2-1.5.5-.4-.8-1.2-1.3-2.1-1.3-.4 0-.8.1-1.1.3V5.9"
        "c0-1.4-1-2.4-2.4-2.4z")
FAUST = ("M9.5 12.5c0-1.2 1-2.1 2.2-2.1.6 0 1.1.2 1.5.6.4-.8 1.2-1.3 2.1-1.3s1.7.5 2.1 1.3"
         "c.4-.4 1-.6 1.6-.6 1.2 0 2.2 1 2.2 2.2v.2c.3-.1.6-.2.9-.2 1.2 0 2.2 1 2.2 2.2v5.6"
         "c0 3.4-2.8 6.1-6.1 6.1h-2.9c-1.9 0-3.6-.8-4.8-2.2l-2.6-3c-.8-.9-.7-2.3.2-3.1.9-.8 2.2-.7 3 .1"
         "l.4.4z")


def _svg(inhalt, groesse=32):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{groesse}" height="{groesse}" viewBox="0 0 32 32">'
            f'{inhalt}</svg>')


def _form(d, fuell, umriss=UMRISS, breite=1.6):
    return (f'<path d="{d}" fill="{fuell}" stroke="{umriss}" stroke-width="{breite}" '
            f'stroke-linejoin="round" stroke-linecap="round"/>')


def _pfeil(p):
    return _form(PFEIL, p["akzent"])


def _doppelpfeil(winkel, p):
    d = "M4 16 L9 11 L9 14 L23 14 L23 11 L28 16 L23 21 L23 18 L9 18 L9 21 Z"
    return f'<g transform="rotate({winkel} 16 16)">{_form(d, p["akzent"])}</g>'


def _mutter(p, drehung, x=16, y=16, s=1.25):
    return (f'<g transform="translate({x - 10 * s} {y - 10 * s}) scale({s}) rotate({drehung} 10 10)">'
            f'<polygon points="{SECHSECK}" fill="{p["akzent"]}" stroke="{UMRISS}" stroke-width="1.4" '
            f'stroke-linejoin="round"/><circle cx="10" cy="10" r="3.2" fill="{UMRISS}"/></g>')


def _lade(p, art, i, n, x=16, y=16, s=1.25):
    """Bild i von n der Ladeanimation."""
    if art == "mutter":
        # Sechskant: nach 60 Grad sieht er wieder gleich aus
        return _mutter(p, i * 60 / n, x, y, s)
    if art == "cursor":
        an = i < n // 2
        return (f'<g transform="translate({x - 10 * s} {y - 10 * s}) scale({s})">'
                f'<path d="M3 5 L8 10 L3 15" fill="none" stroke="{UMRISS}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
                f'<path d="M3 5 L8 10 L3 15" fill="none" stroke="{p["akzent"]}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>'
                + (f'<rect x="10" y="13" width="8" height="3.4" rx="1" fill="{p["akzent"]}" stroke="{UMRISS}" stroke-width="1"/>' if an else "")
                + '</g>')
    # schichten
    sichtbar = 1 + (i * 5 // n)
    teile = [f'<rect x="3" y="3" width="3.5" height="14" rx="1" fill="{p["text"]}" stroke="{UMRISS}" stroke-width="0.8"/>']
    for k, (bx, by, bb) in enumerate([(7.5, 3, 7), (7.5, 6.6, 9), (7.5, 10.2, 10), (7.5, 13.8, 9)][:max(0, sichtbar - 1)]):
        teile.append(f'<rect x="{bx}" y="{by}" width="{bb}" height="3" rx="1.5" fill="{p["akzent"]}" stroke="{UMRISS}" stroke-width="0.6"/>')
    return f'<g transform="translate({x - 10 * s} {y - 10 * s}) scale({s})">{"".join(teile)}</g>'


def zeiger_bilder(p, ladeart):
    """name -> (hotspot im 32er Raster, [svg, ...], verzoegerung ms)"""
    a, g = p["akzent"], p["gefahr"]
    z = {}
    z["default"] = ((4, 2), [_svg(_pfeil(p))], 0)
    z["pointer"] = ((12, 4), [_svg(_form(HAND, a))], 0)
    z["text"] = ((16, 16), [_svg(
        f'<path d="M11 5 h4 l1 1 1-1 h4 M16 6 V26 M11 27 h4 l1-1 1 1 h4" fill="none" stroke="{UMRISS}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M11 5 h4 l1 1 1-1 h4 M16 6 V26 M11 27 h4 l1-1 1 1 h4" fill="none" stroke="{a}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')], 0)
    n = 12 if ladeart == "mutter" else (8 if ladeart == "cursor" else 10)
    verz = 60 if ladeart == "mutter" else (110 if ladeart == "cursor" else 120)
    z["wait"] = ((16, 16), [_svg(_lade(p, ladeart, i, n)) for i in range(n)], verz)
    z["progress"] = ((4, 2), [_svg(_pfeil(p) + _lade(p, ladeart, i, n, 23, 24, 0.75)) for i in range(n)], verz)
    z["crosshair"] = ((16, 16), [_svg(
        f'<path d="M16 3v9M16 20v9M3 16h9M20 16h9" stroke="{UMRISS}" stroke-width="4" stroke-linecap="round"/>'
        f'<path d="M16 3v9M16 20v9M3 16h9M20 16h9" stroke="{a}" stroke-width="2" stroke-linecap="round"/>'
        f'<circle cx="16" cy="16" r="1.6" fill="{a}" stroke="{UMRISS}" stroke-width="0.8"/>')], 0)
    z["move"] = ((16, 16), [_svg(_doppelpfeil(0, p) + _doppelpfeil(90, p))], 0)
    z["not-allowed"] = ((16, 16), [_svg(
        f'<circle cx="16" cy="16" r="10" fill="none" stroke="{UMRISS}" stroke-width="6"/>'
        f'<circle cx="16" cy="16" r="10" fill="none" stroke="{g}" stroke-width="3.6"/>'
        f'<path d="M9 9 L23 23" stroke="{UMRISS}" stroke-width="6"/><path d="M9 9 L23 23" stroke="{g}" stroke-width="3.6"/>')], 0)
    z["help"] = ((4, 2), [_svg(_pfeil(p) +
        f'<circle cx="24" cy="23" r="6.5" fill="{p["akzent2"]}" stroke="{UMRISS}" stroke-width="1.4"/>'
        f'<path d="M22 21.2a2 2 0 1 1 2.6 1.9c-.4.2-.6.5-.6 1M24 26.2v.1" fill="none" stroke="{UMRISS}" stroke-width="1.6" stroke-linecap="round"/>')], 0)
    z["ew-resize"] = ((16, 16), [_svg(_doppelpfeil(0, p))], 0)
    z["ns-resize"] = ((16, 16), [_svg(_doppelpfeil(90, p))], 0)
    z["nwse-resize"] = ((16, 16), [_svg(_doppelpfeil(45, p))], 0)
    z["nesw-resize"] = ((16, 16), [_svg(_doppelpfeil(-45, p))], 0)
    z["grab"] = ((14, 8), [_svg(_form(HAND, a))], 0)
    z["grabbing"] = ((15, 14), [_svg(_form(FAUST, a))], 0)
    z["copy"] = ((4, 2), [_svg(_pfeil(p) +
        f'<circle cx="24" cy="24" r="6" fill="#3fbf6f" stroke="{UMRISS}" stroke-width="1.4"/>'
        f'<path d="M24 21v6M21 24h6" stroke="{UMRISS}" stroke-width="1.8" stroke-linecap="round"/>')], 0)
    z["alias"] = ((4, 2), [_svg(_pfeil(p) +
        f'<circle cx="24" cy="24" r="6" fill="{p["akzent2"]}" stroke="{UMRISS}" stroke-width="1.4"/>'
        f'<path d="M21.5 26.5 L26 22 M23 22 H26 V25" fill="none" stroke="{UMRISS}" stroke-width="1.6" stroke-linecap="round"/>')], 0)
    z["context-menu"] = ((4, 2), [_svg(_pfeil(p) +
        f'<rect x="19" y="18" width="11" height="11" rx="2" fill="{p["karte"]}" stroke="{UMRISS}" stroke-width="1.2"/>'
        f'<path d="M21.5 21h6M21.5 23.5h6M21.5 26h6" stroke="{a}" stroke-width="1.2"/>')], 0)
    z["zoom-in"] = ((13, 13), [_svg(
        f'<circle cx="13" cy="13" r="8" fill="none" stroke="{UMRISS}" stroke-width="5"/>'
        f'<circle cx="13" cy="13" r="8" fill="none" stroke="{a}" stroke-width="2.6"/>'
        f'<path d="M19 19 L27 27" stroke="{UMRISS}" stroke-width="6" stroke-linecap="round"/>'
        f'<path d="M19 19 L27 27" stroke="{a}" stroke-width="3.4" stroke-linecap="round"/>'
        f'<path d="M13 9.5v7M9.5 13h7" stroke="{p["text"]}" stroke-width="1.8" stroke-linecap="round"/>')], 0)
    z["zoom-out"] = ((13, 13), [_svg(
        f'<circle cx="13" cy="13" r="8" fill="none" stroke="{UMRISS}" stroke-width="5"/>'
        f'<circle cx="13" cy="13" r="8" fill="none" stroke="{a}" stroke-width="2.6"/>'
        f'<path d="M19 19 L27 27" stroke="{UMRISS}" stroke-width="6" stroke-linecap="round"/>'
        f'<path d="M19 19 L27 27" stroke="{a}" stroke-width="3.4" stroke-linecap="round"/>'
        f'<path d="M9.5 13h7" stroke="{p["text"]}" stroke-width="1.8" stroke-linecap="round"/>')], 0)
    return z


# Weitere Namen, die Programme verwenden -> auf unsere Grundzeiger verlinken
ALIASE = {
    "default": ["left_ptr", "arrow", "top_left_arrow", "left_arrow"],
    "pointer": ["hand2", "hand1", "pointing_hand", "hand", "e29285e634086352946a0e7090d73106", "9d800788f1b08800ae810202380a0822"],
    "text": ["xterm", "ibeam", "vertical-text"],
    "wait": ["watch", "0426c94ea35c87780ff01dc239897213"],
    "progress": ["left_ptr_watch", "half-busy", "08e8e1c95fe2fc01f976f1e063a24ccd", "3ecb610c1bf2410f44200f48c40d3599"],
    "crosshair": ["cross", "tcross", "cell", "plus", "color-picker"],
    "move": ["fleur", "all-scroll", "size_all", "4498f0e0c1937ffe01fd06f973665830", "9081237383d90e509aa00f00170e968f"],
    "not-allowed": ["forbidden", "no-drop", "circle", "crossed_circle", "03b6e0fcb3499374a867c041f52298f0"],
    "help": ["question_arrow", "whats_this", "left_ptr_help", "d9ce0ab605698f320427677b458ad60b", "5c6cd98b3f3ebcb1f9c7f1c204630408"],
    "ew-resize": ["e-resize", "w-resize", "sb_h_double_arrow", "h_double_arrow", "size_hor", "col-resize", "split_h",
                  "right_side", "left_side", "028006030e0e7ebffc7f7070c0600140", "14fef782d02440884392942c11205230"],
    "ns-resize": ["n-resize", "s-resize", "sb_v_double_arrow", "v_double_arrow", "size_ver", "row-resize", "split_v",
                  "top_side", "bottom_side", "00008160000006810000408080010102", "2870a09082c103050810ffdffffe0204"],
    "nwse-resize": ["nw-resize", "se-resize", "size_fdiag", "bd_double_arrow", "top_left_corner", "bottom_right_corner",
                    "c7088f0f3e6c8088236ef8e1e3e70000", "38c5dff7c7b8962045400281044508d2"],
    "nesw-resize": ["ne-resize", "sw-resize", "size_bdiag", "fd_double_arrow", "top_right_corner", "bottom_left_corner",
                    "fcf1c3c7cd4491d801f1e1c78f100000", "50585d75b494802d0151028115016902"],
    "grab": ["openhand", "fleur-grab", "5aca4d189052212118709018842178c0", "9141b49c8149039304290b508d208c40"],
    "grabbing": ["closedhand", "dnd-move", "dnd-none", "208530c400c041818281048008011002", "fcf21c00b30f7e3f83fe0dfd12e71cff"],
    "copy": ["dnd-copy", "1081e37283d90000800003c07f3ef6bf", "6407b0e94181790501fd1e167b474872", "b66166c04f8c3109214a4fbd64a50fc8"],
    "alias": ["link", "dnd-link", "3085a0e285430894940527032f8b26df", "640fb0e74195791501fd1ed57b41487f", "a2a266d0498c3104214a47bd64ab0fc8"],
    "context-menu": [],
    "zoom-in": [],
    "zoom-out": [],
}


def erzeugen(p, ladeart, ziel: Path, name):
    """Schreibt das Zeigerthema nach ziel/<name>/ (wie ~/.local/share/icons)."""
    if not shutil.which("xcursorgen") or not shutil.which("rsvg-convert"):
        return None
    d = ziel / name
    if d.exists():
        shutil.rmtree(d)
    (d / "cursors").mkdir(parents=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for zname, ((hx, hy), bilder, verz) in zeiger_bilder(p, ladeart).items():
            zeilen = []
            for i, s in enumerate(bilder):
                quelle = tmp / f"{zname}-{i}.svg"
                quelle.write_text(s, encoding="utf-8")
                for g in GROESSEN:
                    png = tmp / f"{zname}-{i}-{g}.png"
                    subprocess.run(["rsvg-convert", "-w", str(g), "-h", str(g), "-o", str(png), str(quelle)], check=True)
                    f = g / 32
                    zeile = f"{g} {round(hx * f)} {round(hy * f)} {png}"
                    if verz:
                        zeile += f" {verz}"
                    zeilen.append(zeile)
            cfg = tmp / f"{zname}.cfg"
            cfg.write_text("\n".join(zeilen) + "\n", encoding="utf-8")
            subprocess.run(["xcursorgen", str(cfg), str(d / "cursors" / zname)], check=True)
            for alias in ALIASE.get(zname, []):
                (d / "cursors" / alias).symlink_to(zname)
    (d / "index.theme").write_text(f"[Icon Theme]\nName={name}\nComment=Biblix-Mauszeiger\nInherits=breeze_cursors\n",
                                   encoding="utf-8")
    (d / "cursor.theme").write_text(f"[Icon Theme]\nInherits={name}\n", encoding="utf-8")
    return d
