#!/bin/bash
# Pruefsumme einer fertigen Biblix-ISO mit dem Biblix-Schluessel signieren (lokal, dort wo der private
# Schluessel liegt; nie in GitHub Actions). Ergebnis: <ISO>.sha256.sig neben der ISO.
#   bash pakete/iso-signieren.sh Biblix-2.0-amd64.iso
# Pruefen (jeder): gpgv --keyring pakete/biblix-archive-keyring.gpg Biblix-2.0-amd64.iso.sha256.sig Biblix-2.0-amd64.iso.sha256
set -euo pipefail
ISO="${1:?Aufruf: iso-signieren.sh DATEI.iso}"
[ -f "$ISO" ] || { echo "$ISO fehlt."; exit 1; }
[ -f "$ISO.sha256" ] || sha256sum "$ISO" > "$ISO.sha256"
sha256sum -c "$ISO.sha256"
gpg --batch --yes --local-user "Biblix Paketquelle" --detach-sign -o "$ISO.sha256.sig" "$ISO.sha256"
gpgv --keyring "$(dirname "$0")/biblix-archive-keyring.gpg" "$ISO.sha256.sig" "$ISO.sha256"
echo "Signiert: $ISO.sha256.sig"
