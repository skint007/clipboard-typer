import logging
import os
import subprocess
import threading
from pathlib import Path
from typing import Callable

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:
    tk = None  # type: ignore[assignment]
    ttk = None  # type: ignore[assignment]
    messagebox = None  # type: ignore[assignment]

from clipboard_typer.config import (
    AppConfig,
    HotkeyConfig,
    PlatformConfig,
    TypingConfig,
    save_config,
)

logger = logging.getLogger(__name__)

_dialog_lock = threading.Lock()


def _detect_dark_mode() -> bool:
    """Detect whether the system is using a dark theme."""
    # GNOME / KDE with xdg-desktop-portal
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True, text=True, timeout=2,
        )
        if "prefer-dark" in result.stdout:
            return True
        if "prefer-light" in result.stdout or "default" in result.stdout:
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # GTK_THEME env var (e.g. "Adwaita:dark")
    gtk_theme = os.environ.get("GTK_THEME", "")
    if ":dark" in gtk_theme.lower():
        return True

    return True  # default to dark


class _Theme:
    """Color palette for the dialog."""

    def __init__(self, dark: bool):
        if dark:
            self.bg = "#2b2b2b"
            self.fg = "#e0e0e0"
            self.fg_dim = "#888888"
            self.frame_bg = "#333333"
            self.entry_bg = "#3c3c3c"
            self.entry_fg = "#e0e0e0"
            self.entry_border = "#555555"
            self.btn_bg = "#444444"
            self.btn_active = "#555555"
            self.btn_primary_bg = "#0078d4"
            self.btn_primary_fg = "#ffffff"
            self.toggle_on = "#0078d4"
            self.toggle_off = "#555555"
            self.toggle_knob = "#ffffff"
        else:
            self.bg = "#f0f0f0"
            self.fg = "#1a1a1a"
            self.fg_dim = "#666666"
            self.frame_bg = "#ffffff"
            self.entry_bg = "#ffffff"
            self.entry_fg = "#1a1a1a"
            self.entry_border = "#cccccc"
            self.btn_bg = "#e0e0e0"
            self.btn_active = "#d0d0d0"
            self.btn_primary_bg = "#0078d4"
            self.btn_primary_fg = "#ffffff"
            self.toggle_on = "#0078d4"
            self.toggle_off = "#cccccc"
            self.toggle_knob = "#ffffff"


class SettingsDialog:
    def __init__(self, config: AppConfig, config_path: Path,
                 on_save: Callable[[AppConfig, bool], None]):
        self._config = config
        self._config_path = config_path
        self._on_save = on_save

    def open(self) -> None:
        if not _dialog_lock.acquire(blocking=False):
            logger.debug("Settings dialog already open")
            return
        try:
            self._build_and_run()
        except Exception:
            logger.exception("Failed to open settings dialog")
        finally:
            _dialog_lock.release()

    def _build_and_run(self) -> None:
        theme = _Theme(_detect_dark_mode())

        root = tk.Tk()
        root.title("Clipboard Typer Settings")
        root.resizable(False, False)
        root.configure(bg=theme.bg)

        style = ttk.Style(root)
        style.theme_use("clam")

        style.configure(".", background=theme.bg, foreground=theme.fg,
                        fieldbackground=theme.entry_bg, borderwidth=0)
        style.configure("TFrame", background=theme.bg)
        style.configure("TLabel", background=theme.bg, foreground=theme.fg)
        style.configure("TLabelframe", background=theme.bg, foreground=theme.fg)
        style.configure("TLabelframe.Label", background=theme.bg,
                        foreground=theme.fg_dim)
        style.configure("TEntry", fieldbackground=theme.entry_bg,
                        foreground=theme.entry_fg, bordercolor=theme.entry_border,
                        insertcolor=theme.entry_fg)
        style.configure("TButton", background=theme.btn_bg, foreground=theme.fg,
                        borderwidth=1, relief="flat", padding=(12, 4))
        style.map("TButton",
                  background=[("active", theme.btn_active)])
        style.configure("Primary.TButton", background=theme.btn_primary_bg,
                        foreground=theme.btn_primary_fg)
        style.map("Primary.TButton",
                  background=[("active", theme.btn_primary_bg)])

        pad = {"padx": 10, "pady": 5}

        # --- Hotkey section ---
        hotkey_frame = ttk.LabelFrame(root, text="Hotkey", padding=10)
        hotkey_frame.grid(row=0, column=0, sticky="ew", **pad)
        hotkey_frame.columnconfigure(1, weight=1)

        ttk.Label(hotkey_frame, text="Combo").grid(row=0, column=0, sticky="w")
        combo_var = tk.StringVar(value=self._config.hotkey.combo)
        ttk.Entry(hotkey_frame, textvariable=combo_var, width=25).grid(
            row=0, column=1, sticky="ew", padx=(8, 0)
        )

        # --- Typing section ---
        typing_frame = ttk.LabelFrame(root, text="Typing", padding=10)
        typing_frame.grid(row=1, column=0, sticky="ew", **pad)
        typing_frame.columnconfigure(1, weight=1)

        ttk.Label(typing_frame, text="Delay (ms)").grid(row=0, column=0, sticky="w")
        delay_var = tk.StringVar(value=str(self._config.typing.delay_ms))
        ttk.Entry(typing_frame, textvariable=delay_var, width=10).grid(
            row=0, column=1, sticky="w", padx=(8, 0)
        )

        ttk.Label(typing_frame, text="Chunk size").grid(row=1, column=0, sticky="w")
        chunk_var = tk.StringVar(value=str(self._config.typing.chunk_size))
        ttk.Entry(typing_frame, textvariable=chunk_var, width=10).grid(
            row=1, column=1, sticky="w", padx=(8, 0)
        )

        ttk.Label(typing_frame, text="Start delay (ms)").grid(
            row=2, column=0, sticky="w"
        )
        start_delay_var = tk.StringVar(value=str(self._config.typing.start_delay_ms))
        ttk.Entry(typing_frame, textvariable=start_delay_var, width=10).grid(
            row=2, column=1, sticky="w", padx=(8, 0)
        )

        compensate_var = tk.BooleanVar(value=self._config.typing.compensate_indent)
        _ToggleRow(typing_frame, "Compensate auto-indent", compensate_var,
                   theme).grid(row=3, column=0, columnspan=2, sticky="ew",
                               pady=(6, 0))

        # --- Platform section ---
        platform_frame = ttk.LabelFrame(root, text="Platform", padding=10)
        platform_frame.grid(row=2, column=0, sticky="ew", **pad)
        platform_frame.columnconfigure(0, weight=1)

        prefer_native_var = tk.BooleanVar(value=self._config.platform.prefer_native)
        _ToggleRow(platform_frame, "Prefer native backend (pynput)",
                   prefer_native_var, theme).grid(row=0, column=0, sticky="ew")

        # --- Buttons ---
        btn_frame = ttk.Frame(root)
        btn_frame.grid(row=3, column=0, sticky="e", **pad)

        def on_save():
            delay = _validate_int("Delay (ms)", delay_var.get())
            chunk = _validate_int("Chunk size", chunk_var.get())
            start_delay = _validate_int("Start delay (ms)", start_delay_var.get())
            if delay is None or chunk is None or start_delay is None:
                return

            new_config = AppConfig(
                hotkey=HotkeyConfig(combo=combo_var.get().strip()),
                typing=TypingConfig(
                    delay_ms=delay,
                    chunk_size=chunk,
                    start_delay_ms=start_delay,
                    compensate_indent=compensate_var.get(),
                ),
                platform=PlatformConfig(prefer_native=prefer_native_var.get()),
            )

            try:
                save_config(new_config, self._config_path)
            except OSError as e:
                messagebox.showerror("Save failed", f"Could not write config: {e}")
                return

            hotkey_changed = new_config.hotkey.combo != self._config.hotkey.combo
            self._on_save(new_config, hotkey_changed)

            if hotkey_changed:
                messagebox.showinfo(
                    "Restart required",
                    "Hotkey changed. Restart the service for it to take effect:\n\n"
                    "systemctl --user restart clipboard-typer",
                )

            root.destroy()

        def on_cancel():
            root.destroy()

        ttk.Button(btn_frame, text="Cancel", command=on_cancel).grid(
            row=0, column=0, padx=(0, 6)
        )
        ttk.Button(btn_frame, text="Save", command=on_save,
                   style="Primary.TButton").grid(row=0, column=1)

        root.protocol("WM_DELETE_WINDOW", on_cancel)
        root.mainloop()


class _ToggleRow(ttk.Frame):
    """A row with a label and a toggle switch."""

    _WIDTH = 40
    _HEIGHT = 22
    _PAD = 3

    def __init__(self, parent, text: str, variable, theme: _Theme):
        super().__init__(parent)
        self._var = variable
        self._theme = theme

        ttk.Label(self, text=text).pack(side="left")

        self._canvas = tk.Canvas(self, width=self._WIDTH, height=self._HEIGHT,
                                 highlightthickness=0, bg=theme.bg, cursor="hand2")
        self._canvas.pack(side="right", padx=(8, 0))
        self._canvas.bind("<Button-1>", self._toggle)

        self._draw()
        self._var.trace_add("write", lambda *_: self._draw())

    def _draw(self):
        c = self._canvas
        c.delete("all")
        on = self._var.get()
        w, h, p = self._WIDTH, self._HEIGHT, self._PAD
        r = h // 2
        knob_r = r - p

        track_color = self._theme.toggle_on if on else self._theme.toggle_off
        # Track (rounded rectangle via two circles + rect)
        c.create_oval(0, 0, h, h, fill=track_color, outline="")
        c.create_oval(w - h, 0, w, h, fill=track_color, outline="")
        c.create_rectangle(r, 0, w - r, h, fill=track_color, outline="")

        # Knob
        cx = w - r if on else r
        c.create_oval(cx - knob_r, p, cx + knob_r, h - p,
                      fill=self._theme.toggle_knob, outline="")

    def _toggle(self, _event=None):
        self._var.set(not self._var.get())


def _validate_int(name: str, value: str, min_val: int = 0) -> int | None:
    """Validate a string as a non-negative integer. Returns the int or None."""
    try:
        n = int(value)
    except ValueError:
        messagebox.showerror("Invalid value", f"{name} must be an integer.")
        return None
    if n < min_val:
        messagebox.showerror("Invalid value", f"{name} must be >= {min_val}.")
        return None
    return n
