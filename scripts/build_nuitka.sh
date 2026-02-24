#!/bin/bash
set -euo pipefail

python -m nuitka \
    --onefile \
    --output-filename=clipboard-typer-nuitka \
    --include-package=pynput \
    --include-package=pystray \
    --include-package=PIL \
    --include-module=pyperclip \
    --include-module=tkinter \
    --include-module=_tkinter \
    --follow-imports \
    --assume-yes-for-downloads \
    src/clipboard_typer/app.py
