#!/bin/bash
# Paketquelle (paketquelle/) auf GitHub Pages veroeffentlichen (Zweig gh-pages).
# Laeuft in Git Bash unter Windows (GitHub-Anmeldung ueber gh):
#   bash pakete/veroeffentlichen.sh "Kurze Beschreibung"
set -euo pipefail
cd "$(dirname "$0")/.."
MSG="${1:-Paketquelle aktualisiert}"
[ -f paketquelle/InRelease ] || { echo "paketquelle/ ist leer: erst bash pakete/bauen.sh (in WSL)"; exit 1; }
W=$(mktemp -d)
trap 'rm -rf "$W"' EXIT
git clone -q --branch gh-pages --single-branch "$(git remote get-url origin)" "$W/p"
cd "$W/p"
git config user.name "$(git -C "$OLDPWD" config user.name)"
git config user.email "$(git -C "$OLDPWD" config user.email)"
git config core.autocrlf false
find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -a "$OLDPWD/paketquelle/." .
printf '* -text\n' > .gitattributes
git add -A
if git diff --cached --quiet; then
    echo "Nichts Neues zu veroeffentlichen."
    exit 0
fi
git commit -q -F - <<EOF
Paketquelle: $MSG

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
EOF
git push -q origin gh-pages
echo "Veroeffentlicht. Biblix-PCs sehen das Update nach der naechsten Paketlisten-Aktualisierung."
