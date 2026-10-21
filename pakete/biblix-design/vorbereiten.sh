#!/bin/bash
# biblix-design: Grafiken und Schriften aus den SVG-Quellen erzeugen (beim Paketbau, nicht beim Nutzer).
#   vorbereiten.sh <paketbaum>
set -euo pipefail
P="$1"
BR="$P/usr/share/biblix/branding"
GS="$P/usr/share/biblix/grub"
T="$P/usr/share/desktop-base/biblix-theme"
GT="$P/usr/share/grub/themes/biblix"
PL="$P/usr/share/plymouth/themes/biblix"
png() { rsvg-convert -w "$2" -h "$3" -o "$4" "$1"; }

# Icons in allen Groessen
for s in 16 22 24 32 48 64 128 256; do
    mkdir -p "$P/usr/share/icons/hicolor/${s}x${s}/apps"
    png "$BR/biblix-logo.svg" $s $s "$P/usr/share/icons/hicolor/${s}x${s}/apps/biblix.png"
    png "$P/usr/share/icons/hicolor/scalable/apps/s-launcher.svg" $s $s "$P/usr/share/icons/hicolor/${s}x${s}/apps/s-launcher.png"
done
mkdir -p "$P/usr/share/pixmaps"
png "$BR/biblix-logo.svg" 256 256 "$P/usr/share/pixmaps/biblix.png"

# Hintergrund, Anmeldebild und GRUB-Bild fuer desktop-base
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

# Bootmenue des installierten Systems
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

# Bootanimation
png "$BR/biblix-logo.svg" 160 160 "$PL/logo.png"
png "$BR/bar-track.svg" 240 6 "$PL/bar-track.png"
png "$BR/bar-fill.svg" 240 6 "$PL/bar-fill.png"
