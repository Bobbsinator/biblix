#!/bin/bash
# Rauchtest einer fertigen Biblix-ISO in QEMU (UEFI). Macht Bildschirmfotos vom Bootmenue und vom Live-Desktop
# und bricht ab, wenn das System nicht bis zur Anmeldung kommt. Mit --secureboot startet es mit Secure Boot an.
#   ./iso-testen.sh Biblix-2.0-amd64.iso [--secureboot]
# Braucht: qemu-system-x86, ovmf, imagemagick (fuer die Fotos). Mit KVM (/dev/kvm) in Minuten, ohne deutlich laenger.
set -euo pipefail
ISO="${1:?Aufruf: iso-testen.sh DATEI.iso [--secureboot]}"
SB="${2:-}"
AUS="iso-test-$(date +%Y%m%d-%H%M)"
mkdir -p "$AUS"
for t in qemu-system-x86_64 convert; do command -v $t >/dev/null || { echo "$t fehlt (apt install qemu-system-x86 ovmf imagemagick)"; exit 1; }; done
if [ "$SB" = --secureboot ]; then
    CODE=/usr/share/OVMF/OVMF_CODE_4M.secboot.fd; VARS=/usr/share/OVMF/OVMF_VARS_4M.ms.fd
else
    CODE=/usr/share/OVMF/OVMF_CODE_4M.fd; VARS=/usr/share/OVMF/OVMF_VARS_4M.fd
fi
cp "$VARS" "$AUS/vars.fd"
BESCHL=""; [ -w /dev/kvm ] && BESCHL="-enable-kvm -cpu host"
MON="$AUS/monitor.sock"
qemu-system-x86_64 $BESCHL -machine q35,smm=on -m 6144 -smp 4 \
    -global driver=cfi.pflash01,property=secure,value=on \
    -drive if=pflash,format=raw,unit=0,file="$CODE",readonly=on \
    -drive if=pflash,format=raw,unit=1,file="$AUS/vars.fd" \
    -cdrom "$ISO" -boot d -vga virtio -display none \
    -monitor unix:"$MON",server,nowait -serial file:"$AUS/serial.log" &
QEMU=$!
trap 'kill $QEMU 2>/dev/null || true' EXIT
foto() {   # foto NAME
    printf 'screendump %s\n' "$PWD/$AUS/$1.ppm" | socat - UNIX-CONNECT:"$MON" >/dev/null 2>&1 || \
        printf 'screendump %s\n' "$PWD/$AUS/$1.ppm" | python3 -c "
import socket,sys; s=socket.socket(socket.AF_UNIX); s.connect('$MON'); s.sendall(sys.stdin.buffer.read())"
    sleep 2
    [ -f "$AUS/$1.ppm" ] && convert "$AUS/$1.ppm" "$AUS/$1.png" && rm -f "$AUS/$1.ppm" && echo "Foto: $AUS/$1.png"
}
WARTE=${WARTE:-1}; [ -n "$BESCHL" ] || WARTE=4   # ohne KVM alles viermal langsamer
sleep $((20 * WARTE)); foto 1-bootmenue
sleep $((150 * WARTE)); foto 2-live-desktop
sleep $((60 * WARTE)); foto 3-willkommen
kill -0 $QEMU 2>/dev/null && echo "QEMU laeuft noch: System ist nicht abgestuerzt." || { echo "FEHLER: QEMU beendet."; exit 1; }
echo "Fertig. Fotos in $AUS/ ansehen: Bootmenue, Live-Desktop, Willkommens-Assistent."
