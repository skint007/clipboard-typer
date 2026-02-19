# Clipboard Typer

A lightweight utility that types out clipboard contents keystroke-by-keystroke into the active window. Designed for situations where paste is blocked or unavailable.

## Problem

Some applications, login fields, remote desktops, and terminal interfaces block `Ctrl+V` paste. This tool bypasses that limitation by simulating individual key presses, making it appear as if the user is physically typing.

## Features

- **Global hotkey activation** — trigger from any window without switching focus
- **Clipboard reading** — grabs current clipboard content on demand
- **Keystroke simulation** — types text character-by-character into the focused window
- **Configurable typing speed** — adjustable delay between keystrokes to avoid dropped characters
- **Wayland & X11 support** — fallback to `wtype`/`xdotool` when native input simulation is restricted
- **System tray indicator** — optional tray icon showing active/idle status
- **Multi-platform** — works on Linux, Windows, and macOS

## Tech Stack

| Component | Tool | Purpose |
|---|---|---|
| Language | Python 3.12+ | Core application logic |
| Hotkey Listener | `pynput` | Global keybind detection |
| Keystroke Simulation | `pynput.keyboard.Controller` | Typing text into active window |
| Clipboard Access | `pyperclip` | Reading system clipboard contents |
| Wayland Fallback | `wtype` (subprocess) | Keystroke sim on Wayland compositors |
| X11 Fallback | `xdotool` (subprocess) | Keystroke sim on X11 if pynput fails |
| Config | TOML (`tomllib` / `tomli`) | User-configurable hotkeys and settings |
| Packaging | `PyInstaller` or `zipapp` | Single-file distribution |

## Configuration (example)

```toml
[hotkey]
combo = "ctrl+shift+v"

[typing]
delay_ms = 10          # ms between keystrokes
chunk_size = 0         # 0 = type all at once

[platform]
prefer_native = true   # use pynput first, fall back to wtype/xdotool
```