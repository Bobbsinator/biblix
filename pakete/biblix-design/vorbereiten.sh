#!/bin/bash
# biblix-design: Grafiken, Klaenge und Schriften aus den Quellen erzeugen (beim Paketbau, nicht beim Nutzer).
#   vorbereiten.sh <paketbaum>
set -euo pipefail
P="$1"
BR="$P/usr/share/biblix/branding"
GS="$P/usr/share/biblix/grub"
T="$P/usr/share/desktop-base/biblix-theme"
GT="$P/usr/share/grub/themes/biblix"
PL="$P/usr/share/plymouth/themes/biblix"
D="$P/usr/share/biblix/design"
png() { rsvg-convert -w "$2" -h "$3" -o "$4" "$1"; }

# Python-Teile des Designs (Generatoren) im Paketbaum verwenden
export BIBLIX_DESIGN_DIR="$D"
PY="python3 -B"

# --- Standard-Hintergrund (Schrauben-Bauplan in Bibi Tech) und Firmenlogos
$PY - "$D" "$BR" <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1] + "/lib")
from biblix_design import kern, hintergruende, grafik
d, br = Path(sys.argv[1]), Path(sys.argv[2])
p = kern.palette(dict(kern.STANDARD), "dunkel")
(br / "wallpaper.svg").write_text(hintergruende.svg("schrauben-bauplan", p), encoding="utf-8")
logos = d / "logos"
logos.mkdir(exist_ok=True)
for pid, f in grafik.FIRMENLOGOS.items():
    (logos / f"{pid}.svg").write_text(f(), encoding="utf-8")
# App-Symbol "Biblix Design" (Palette auf Kachel)
icon = Path(sys.argv[1]).parents[1] / "icons/hicolor/scalable/apps/de.biblix.Design.svg"
icon.parent.mkdir(parents=True, exist_ok=True)
icon.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">'
                '<rect x="3" y="3" width="42" height="42" rx="11" fill="#378add"/>'
                '<path d="M24 11 a13 13 0 1 0 0 26 c2.2 0 2.9 -1.6 1.9 -3.2 -1 -1.6 .2 -3.2 2.1 -3.2 H31 '
                'a6 6 0 0 0 6 -6 c0 -7.6 -5.8 -13.6 -13 -13.6 Z" fill="#ffffff"/>'
                '<circle cx="17.5" cy="22" r="2.4" fill="#e24b4a"/><circle cx="22" cy="16.5" r="2.4" fill="#ffd400"/>'
                '<circle cx="29" cy="17" r="2.4" fill="#1d9e75"/></svg>', encoding="utf-8")
EOF

# --- Klaenge (Synthese, dauert etwas)
mkdir -p "$P/usr/share/sounds"
$PY "$D/lib/biblix_design/klaenge.py" "$P/usr/share/sounds"

# --- Icons in allen Groessen
for s in 16 22 24 32 48 64 128 256; do
    mkdir -p "$P/usr/share/icons/hicolor/${s}x${s}/apps"
    png "$BR/biblix-logo.svg" $s $s "$P/usr/share/icons/hicolor/${s}x${s}/apps/biblix.png"
    png "$P/usr/share/icons/hicolor/scalable/apps/s-launcher.svg" $s $s "$P/usr/share/icons/hicolor/${s}x${s}/apps/s-launcher.png"
    png "$P/usr/share/icons/hicolor/scalable/apps/de.biblix.Design.svg" $s $s "$P/usr/share/icons/hicolor/${s}x${s}/apps/de.biblix.Design.png"
done
mkdir -p "$P/usr/share/pixmaps"
png "$BR/biblix-logo.svg" 256 256 "$P/usr/share/pixmaps/biblix.png"

# --- Hintergrund, Anmeldebild und GRUB-Bild fuer desktop-base
mkdir -p "$T/wallpaper/contents/images" "$T/login" "$T/grub"
for r in 1920x1080 2560x1440 3840x2160; do
    png "$BR/wallpaper.svg" ${r%x*} ${r#*x} "$T/wallpaper/contents/images/$r.png"
done
cp "$T/wallpaper/contents/images/1920x1080.png" "$T/login/background.png"
cp "$BR/wallpaper.svg" "$T/login/background.svg"
png "$BR/wallpaper.svg" 1920 1080 "$T/grub/grub-16x9.png"
png "$BR/wallpaper.svg" 1920 1200 "$T/grub/grub-4x3.png"
mkdir -p "$P/usr/share/wallpapers"
ln -sfn ../desktop-base/biblix-theme/wallpaper "$P/usr/share/wallpapers/Biblix"

# --- Bootmenue des installierten Systems (Grundversion; Biblix Design erzeugt die farbige Fassung)
mkdir -p "$GT/icons"
cp "$GS/theme.txt" "$GT/theme.txt"
png "$GS/background.svg" 1920 1080 "$GT/background.png"
png "$GS/select.svg" 8 8 "$GT/select_c.png"
for p in n s e w nw ne sw se; do png "$GS/select-edge.svg" 3 3 "$GT/select_$p.png"; done
for p in c n s e w nw ne sw se; do png "$GS/menu.svg" 8 8 "$GT/menu_$p.png"; done
for c in biblix debian gnu-linux gnu linux os; do png "$BR/biblix-logo.svg" 48 48 "$GT/icons/$c.png"; done
for c in windows windows10 windows11; do png "$GS/icon-windows.svg" 48 48 "$GT/icons/$c.png"; done
for c in efi recovery memtest; do png "$GS/icon-system.svg" 48 48 "$GT/icons/$c.png"; done
for s in 16 24; do
    grub-mkfont -s $s -o "$GT/dejavu_regular_$s.pf2" /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
    grub-mkfont -s $s -o "$GT/dejavu_bold_$s.pf2" /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
done

# --- Bootanimation (Grundversion)
png "$BR/biblix-logo.svg" 160 160 "$PL/logo.png"
png "$BR/bar-track.svg" 240 6 "$PL/bar-track.png"
png "$BR/bar-fill.svg" 240 6 "$PL/bar-fill.png"

# --- Python-Zwischendateien nie ins Paket
find "$P/usr/share/biblix/design" -name __pycache__ -type d -prune -exec rm -rf {} +
