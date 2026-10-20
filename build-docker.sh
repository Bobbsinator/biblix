#!/bin/bash
# Biblix in einem Debian-13-Container bauen (z. B. unter Ubuntu, Fedora oder WSL mit Docker).
#   ./build-docker.sh
set -euo pipefail
cd "$(dirname "$0")"
docker run --rm --privileged \
    -v "$PWD:/build" -w /build \
    debian:trixie \
    bash -c "apt-get update && apt-get install -y live-build python3 && ./build.sh"
