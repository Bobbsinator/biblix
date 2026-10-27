#!/bin/bash
# Setzt die gerenderten Zeremonien (Bilder + Ton) zu MP4-Filmen zusammen und legt sie ins Paket biblix-zeremonien.
#   kunst/zeremonien/alle_rendern.sh   (Bilder)   dann   kunst/zeremonien/zusammensetzen.sh
set -e
K=$(cd "$(dirname "$0")/.." && pwd)
A=$K/ausgabe/zeremonien
ZIEL=$K/../pakete/biblix-zeremonien/usr/share/biblix/zeremonien
python3 -I $K/zeremonien/klaenge.py $A/ton
[ -f $A/hochfahren/bild_0300.png ] || python3 -I $K/zeremonien/titel.py $A/hochfahren
for n in hochfahren keynote abmelden herunterfahren windows; do
    ffmpeg -loglevel error -y -framerate 24 -i $A/$n/bild_%04d.png -i $A/ton/$n.wav \
        -c:v libx264 -crf 24 -preset slow -pix_fmt yuv420p -af apad -c:a aac -b:a 160k -shortest -movflags +faststart \
        $ZIEL/$n.mp4
    echo "$n: $(du -h $ZIEL/$n.mp4 | cut -f1)"
done
