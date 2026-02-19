#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")"
project_root="$(dirname "$PWD")"

# Build tarball from current source
tar czf "clipboard-typer-0.1.0.tar.gz" \
    --transform 's,^\.,key-sender-0.1.0,' \
    --exclude='./aur' --exclude='./.git' --exclude='__pycache__' \
    --exclude='*.egg-info' --exclude='.pytest_cache' \
    --exclude='./dist' --exclude='./build' \
    -C "$project_root" .

makepkg -sf "$@"
