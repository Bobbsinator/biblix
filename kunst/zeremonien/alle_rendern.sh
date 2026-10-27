#!/bin/bash
# Rendert alle Zeremonien-Filme (Einzelbilder) nach kunst/ausgabe/zeremonien/<name>/
set -e
K=$(cd "$(dirname "$0")/.." && pwd)
A=$K/ausgabe/zeremonien
for n in hochfahren keynote abmelden herunterfahren; do
    mkdir -p $A/$n
    (cd $K/blender/zeremonien && BREITE=${BREITE:-2560} HOEHE=${HOEHE:-1440} blender -b --factory-startup -P $n.py -- $A/$n/bild_ > $A/$n/log.txt 2>&1)
    echo "$n: $(ls $A/$n/bild_*.png | wc -l) Bilder"
done
python3 -I $K/zeremonien/windows.py $A/windows
echo "windows: $(ls $A/windows/bild_*.png | wc -l) Bilder"
