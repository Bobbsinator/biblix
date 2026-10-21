#!/bin/bash
# biblix-system: Verknuepfungen und Sonderrechte (unter Windows/OneDrive nicht moeglich)
set -euo pipefail
P="$1"
mkdir -p "$P/usr/bin" "$P/usr/share/man/man8"
ln -sfn sudo "$P/usr/bin/bibi"
ln -sfn sudo.8.gz "$P/usr/share/man/man8/bibi.8.gz"
chmod 0440 "$P/etc/sudoers.d/biblix"
