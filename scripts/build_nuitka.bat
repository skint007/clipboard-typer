@echo off
python -m nuitka ^
    --onefile ^
    --output-filename=clipboard-typer-nuitka.exe ^
    --include-package=pynput ^
    --include-package=pystray ^
    --include-package=PIL ^
    --include-package=PySide6 ^
    --include-module=pyperclip ^
    --include-data-files=src/clipboard_typer/resources/style.qss=clipboard_typer/resources/style.qss ^
    --follow-imports ^
    --assume-yes-for-downloads ^
    src\clipboard_typer\app.py
