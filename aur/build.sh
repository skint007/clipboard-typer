#!/bin/bash
set -euo pipefail

# Local test build. makepkg clones the package straight from GitHub
# (source=("git+...")), exactly as paw's CI does — so push your changes
# before building if you want them included.

# Deactivate any active virtualenv so makepkg uses system Python
unset VIRTUAL_ENV
export PATH="/usr/bin:$PATH"

cd "$(dirname "$0")"

makepkg -sf "$@"
