#!/bin/bash
# Einmalig: Signierschluessel fuer die Biblix-Paketquelle erzeugen (in WSL als root).
# Oeffentlicher Teil -> pakete/biblix-archive-keyring.gpg (kommt in jedes Biblix)
# Privater Teil bleibt in WSL; Sicherung nach %USERPROFILE%\Biblix-Schluessel (Windows)
set -euo pipefail
cd "$(dirname "$0")"
NAME="Biblix Paketquelle"
if gpg --list-secret-keys "$NAME" >/dev/null 2>&1; then
    echo "Schluessel existiert schon:"; gpg --list-secret-keys --keyid-format long "$NAME"; exit 0
fi
gpg --batch --passphrase '' --quick-gen-key "$NAME <biblix@localhost>" ed25519 sign never
gpg --export "$NAME" > biblix-archive-keyring.gpg
# Windows-Benutzerordner ermitteln (cmd.exe antwortet mit Windows-Zeilenende)
WINUSER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')
BACKUP=${BIBLIX_BACKUP:-/mnt/c/Users/${WINUSER:-Public}/Biblix-Schluessel}
mkdir -p "$BACKUP"
gpg --armor --export-secret-keys "$NAME" > "$BACKUP/biblix-paketquelle-PRIVAT.asc"
gpg --armor --export "$NAME" > "$BACKUP/biblix-paketquelle-oeffentlich.asc"
echo "Fertig. Fingerabdruck:"
gpg --list-keys --with-colons "$NAME" | sed -n 's/^fpr:::::::::\([0-9A-F]*\):$/\1/p' | head -n1
echo "Sicherung: $BACKUP (privat - nicht weitergeben!)"
