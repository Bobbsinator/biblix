"""Gemeinsame Hilfen fuer die Standort-Motive (4K, SVG)."""
import math

W, H = 3840, 2160
MONO = "DejaVu Sans Mono, monospace"
SANS = "DejaVu Sans, sans-serif"
SERIF = "DejaVu Serif, serif"


def svg(inhalt, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<defs>{defs}</defs>{inhalt}</svg>')


def lin(gid, stops, x1=0, y1=0, x2=0, y2=1):
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    return f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>'


def rad(gid, stops, cx=0.5, cy=0.5, r=0.5):
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    return f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">{s}</radialGradient>'


def t(x, y, text, gr=28, farbe="#fff", anker="start", fett=False, schrift=MONO, abstand=2, extra=""):
    f = ' font-weight="bold"' if fett else ""
    return (f'<text x="{x:.0f}" y="{y:.0f}" font-family="{schrift}" font-size="{gr}" fill="{farbe}" '
            f'text-anchor="{anker}" letter-spacing="{abstand}"{f} {extra}>{text}</text>')


def schein(cx, cy, r, gid):
    """Weicher runder Lichtschein (ohne Filter, damit nichts eckig abgeschnitten wird)."""
    return f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="url(#{gid})"/>'


def sechseck(cx, cy, r, drehung=0):
    return " ".join(f"{cx + r * math.cos(math.radians(60 * i - 90 + drehung)):.1f},"
                    f"{cy + r * math.sin(math.radians(60 * i - 90 + drehung)):.1f}" for i in range(6))
