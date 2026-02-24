# clipboard-typer

Type clipboard contents keystroke-by-keystroke into the active window. Designed for situations where paste is blocked or unavailable — remote desktops, restricted login fields, and terminal interfaces that intercept `Ctrl+V`.

## Features

- **Global hotkey** — trigger from any window (default: `Ctrl+Shift+V`)
- **Multiple typing backends** — pynput (native), ydotool, wtype, xdotool
- **Automatic backend selection** — detects Wayland/X11 and picks the best available backend
- **System tray icon** — visual active/paused state with pause/resume toggle
- **Settings GUI** — tkinter dialog with dark mode detection
- **Configurable typing speed** — adjustable delay, chunk size, and start delay
- **Editor indent compensation** — clears auto-indent after newlines
- **Systemd service** — run as a user service on Linux

## Installation

### Arch Linux (AUR)

```bash
yay -S clipboard-typer
```

### pip

```bash
pip install .

# With tray icon support
pip install .[tray]
```

### Optional dependencies

| Package | Purpose |
|---|---|
| `pystray`, `Pillow` | System tray icon |
| `ydotool` | Wayland typing backend (recommended) |
| `wtype` | Alternative Wayland backend |
| `xdotool` | X11 typing backend |
| `wl-clipboard` | Wayland clipboard access |

## Usage

```bash
# Start with defaults
clipboard-typer

# With debug logging
clipboard-typer -v

# Without tray icon
clipboard-typer --no-tray

# Custom config file
clipboard-typer --config /path/to/config.toml
```

Press the hotkey (`Ctrl+Shift+V` by default) while text is in your clipboard. After a short delay, the text is typed character-by-character into the focused window.

### Systemd service

```bash
systemctl --user enable --now clipboard-typer
```

## Configuration

Config file location: `~/.config/clipboard-typer/config.toml`

```toml
start_paused = false

[hotkey]
combo = "ctrl+shift+v"

[typing]
delay_ms = 10              # ms between keystrokes
chunk_size = 0             # characters per chunk (0 = all at once)
start_delay_ms = 300       # ms before typing starts (modifier release time)
compensate_indent = false  # clear editor auto-indent after newlines

[platform]
prefer_native = true       # try pynput first, fall back to system tools
```

## Backend selection

| Platform | prefer_native=true | prefer_native=false |
|---|---|---|
| Windows / macOS | pynput | pynput |
| Wayland | ydotool → wtype → xdotool | ydotool → wtype → xdotool |
| X11 | pynput (fallback: xdotool) | xdotool |

## Development

```bash
# Install dev dependencies
pip install .[dev,tray]

# Run tests
pytest
```

## License

[MIT](LICENSE)
