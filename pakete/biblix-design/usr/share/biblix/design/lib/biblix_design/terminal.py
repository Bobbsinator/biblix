"""Terminal (Konsole): Farbschema und Profil im Biblix-Stil."""
from .kern import kde_rgb, mischen, heller, drehen


def farbschema(p, name):
    hinter = p["grund"] if p["dunkel"] else p["karte"]
    vorne = p["text"]
    a, a2 = p["akzent"], p["akzent2"]
    # 8 Grundfarben: an der Palette ausgerichtet, aber unterscheidbar
    farben = [
        mischen(hinter, vorne, 0.25),           # schwarz
        p["gefahr"],                            # rot
        "#3fbf6f" if p["dunkel"] else "#1f8a4a",  # gruen
        a2,                                     # gelb
        a,                                      # blau -> Akzent
        drehen(a, 60),                          # magenta
        drehen(a, -40),                         # cyan
        mischen(vorne, hinter, 0.15),           # weiss
    ]
    z = [f"[General]", f"Description={name}", "Opacity=1", "Wallpaper=", "",
         "[Background]", f"Color={kde_rgb(hinter)}", "", "[BackgroundIntense]", f"Color={kde_rgb(hinter)}", "",
         "[Foreground]", f"Color={kde_rgb(vorne)}", "", "[ForegroundIntense]", f"Color={kde_rgb(vorne)}", ""]
    for i, f in enumerate(farben):
        z += [f"[Color{i}]", f"Color={kde_rgb(f)}", "",
              f"[Color{i}Intense]", f"Color={kde_rgb(heller(f, 0.2))}", "",
              f"[Color{i}Faint]", f"Color={kde_rgb(mischen(f, hinter, 0.35))}", ""]
    return "\n".join(z)


def profil(schema):
    return f"""[Appearance]
ColorScheme={schema}
Font=DejaVu Sans Mono,11,-1,5,400,0,0,0,0,0,0,0,0,0,0,1

[Cursor Options]
CursorShape=1
UseCustomCursorColor=false

[General]
Name=Biblix
Parent=FALLBACK/
TerminalMargin=10

[Scrolling]
HistorySize=10000
"""

