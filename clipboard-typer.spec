# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = (
    collect_submodules('pynput')
    + collect_submodules('pystray')
    + collect_submodules('PySide6')
    + [
        'PIL.Image',
        'PIL.ImageDraw',
        'pyperclip',
    ]
)

# Bundle the QSS stylesheet
qss_path = os.path.join('src', 'clipboard_typer', 'resources', 'style.qss')
datas = [(qss_path, os.path.join('clipboard_typer', 'resources'))]

a = Analysis(
    ['src/clipboard_typer/app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='clipboard-typer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
