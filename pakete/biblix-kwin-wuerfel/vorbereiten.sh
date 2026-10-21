#!/bin/bash
# biblix-kwin-wuerfel: kompiliert den Würfel-Effekt in der Baukiste (Debian-13-Chroot mit kwin-dev).
#   vorbereiten.sh <paketbaum>
# Die Baukiste legt pakete/baukiste-einrichten.sh an (einmalig).
set -euo pipefail
P="$1"
B=${BAUKISTE:-/root/baukiste}
[ -x "$B/usr/bin/cmake" ] || { echo "Baukiste fehlt: bash pakete/baukiste-einrichten.sh"; exit 1; }
rm -rf "$B/tmp/wuerfel" "$B/tmp/wuerfel-ziel"
cp -r "$P/quelle" "$B/tmp/wuerfel"
chroot "$B" bash -c '
set -e
cd /tmp/wuerfel && mkdir -p bau && cd bau
cmake .. -DCMAKE_INSTALL_PREFIX=/usr -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF >/dev/null
make -j"$(nproc)" >/dev/null
make install DESTDIR=/tmp/wuerfel-ziel >/dev/null
strip --strip-unneeded /tmp/wuerfel-ziel/usr/lib/x86_64-linux-gnu/qt6/plugins/kwin/effects/plugins/biblix_wuerfel.so
'
rm -rf "$P/quelle"
cp -a "$B/tmp/wuerfel-ziel/usr" "$P/"
mkdir -p "$P/usr/share/doc/biblix-kwin-wuerfel"
cat > "$P/usr/share/doc/biblix-kwin-wuerfel/copyright" <<'EOF'
Biblix-Würfel – Portierung von kwin-effects-cube für KWin 6.3
Quelle: https://github.com/zzag/kwin-effects-cube
Copyright: 2022 Vlad Zahorodnii <vlad.zahorodnii@kde.org>
           2026 Biblix (Anpassung: Würfel beim Wechsel der Arbeitsfläche)
Lizenz: GPL-2.0-only OR GPL-3.0-only OR LicenseRef-KDE-Accepted-GPL
 Die vollständigen Lizenztexte liegen in /usr/share/common-licenses/GPL-2 und GPL-3.
EOF
rm -rf "$B/tmp/wuerfel" "$B/tmp/wuerfel-ziel"
