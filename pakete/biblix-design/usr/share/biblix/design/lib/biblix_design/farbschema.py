"""KDE-Farbschema (.colors) aus einer Biblix-Palette."""
from .kern import kde_rgb, mischen, heller, dunkler


def gruppe(p, hinter, hinter_alt, vorne=None):
    vorne = vorne or p["text"]
    return {
        "BackgroundNormal": hinter,
        "BackgroundAlternate": hinter_alt,
        "DecorationFocus": p["akzent"],
        "DecorationHover": p["akzent_hell"],
        "ForegroundNormal": vorne,
        "ForegroundInactive": p["leise"],
        "ForegroundActive": p["akzent"],
        "ForegroundLink": p["akzent"] if p["dunkel"] else p["akzent_dunkel"],
        "ForegroundVisited": mischen(p["akzent"], p["leise"], 0.5),
        "ForegroundNegative": p["gefahr"],
        "ForegroundNeutral": p["akzent2"],
        "ForegroundPositive": "#3fbf6f" if p["dunkel"] else "#1f8a4a",
    }


def erzeugen(p, name):
    titelzeile = p["flaeche"]
    gruppen = {
        "Colors:Window": gruppe(p, p["flaeche"], mischen(p["flaeche"], p["karte"], 0.5)),
        "Colors:View": gruppe(p, p["grund"] if p["dunkel"] else p["karte"],
                              mischen(p["grund"] if p["dunkel"] else p["karte"], p["flaeche"], 0.6)),
        "Colors:Button": gruppe(p, p["karte"], mischen(p["karte"], p["rand"], 0.4)),
        "Colors:Selection": gruppe(p, p["akzent"], p["akzent_dunkel"], p["auf_akzent"]),
        "Colors:Tooltip": gruppe(p, p["karte"], p["flaeche"]),
        "Colors:Complementary": gruppe(p, dunkler(p["grund"], 0.2) if p["dunkel"] else p["text"],
                                       p["grund"], p["text"] if p["dunkel"] else p["karte"]),
        "Colors:Header": gruppe(p, titelzeile, mischen(titelzeile, p["karte"], 0.5)),
        "Colors:Header][Inactive": gruppe(p, p["flaeche"], p["flaeche"], p["leise"]),
    }
    zeilen = [f"[General]", f"ColorScheme={name}", f"Name={name}", "shadeSortColumn=true", "",
              "[KDE]", "contrast=4", "",
              "[ColorEffects:Disabled]", "Color=56,56,56", "ColorAmount=0", "ColorEffect=0",
              "ContrastAmount=0.65", "ContrastEffect=1", "IntensityAmount=0.1", "IntensityEffect=2", "",
              "[ColorEffects:Inactive]", "ChangeSelectionColor=true", "Color=112,111,110", "ColorAmount=0.025",
              "ColorEffect=2", "ContrastAmount=0.1", "ContrastEffect=2", "Enable=false",
              "IntensityAmount=0", "IntensityEffect=0", ""]
    for g, werte in gruppen.items():
        zeilen.append(f"[{g}]")
        zeilen += [f"{k}={kde_rgb(v)}" for k, v in werte.items()]
        zeilen.append("")
    zeilen += ["[WM]",
               f"activeBackground={kde_rgb(titelzeile)}",
               f"activeBlend={kde_rgb(p['akzent'])}",
               f"activeForeground={kde_rgb(p['text'])}",
               f"inactiveBackground={kde_rgb(p['flaeche'])}",
               f"inactiveBlend={kde_rgb(p['flaeche'])}",
               f"inactiveForeground={kde_rgb(p['leise'])}", ""]
    return "\n".join(zeilen)
