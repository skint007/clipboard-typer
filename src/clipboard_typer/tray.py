import logging
import threading
from pathlib import Path
from typing import Callable

from clipboard_typer.config import AppConfig

logger = logging.getLogger(__name__)


class TrayIcon:
    def __init__(self, on_quit: Callable[[], None], paused_event: threading.Event,
                 config: AppConfig, config_path: Path):
        self._on_quit = on_quit
        self._paused_event = paused_event
        self._config = config
        self._config_path = config_path
        self._icon = None
        self._Image = None
        self._ImageDraw = None

    def _create_icon_image(self, paused: bool):
        """Create the tray icon image with visual state indication."""
        S = 64
        image = self._Image.new("RGBA", (S, S), (0, 0, 0, 0))
        draw = self._ImageDraw.Draw(image)

        if paused:
            board = (100, 100, 100, 255)
            clip = (80, 80, 80, 255)
            lines = (70, 70, 70, 255)
        else:
            board = (0, 150, 214, 255)
            clip = (0, 120, 180, 255)
            lines = (255, 255, 255, 200)

        # Clipboard board
        draw.rounded_rectangle([8, 14, 56, 60], radius=5, fill=board)

        # Clip at top (outer)
        draw.rounded_rectangle([20, 4, 44, 20], radius=4, fill=clip)
        # Clip hole (inner cutout)
        draw.rounded_rectangle([25, 7, 39, 16], radius=3, fill=(0, 0, 0, 0))

        # Text lines on clipboard
        for y in (26, 34, 42):
            w = 32 if y < 42 else 20  # shorter last line
            draw.rounded_rectangle([16, y, 16 + w, y + 3], radius=1, fill=lines)

        # Typing cursor on last line
        if not paused:
            draw.rectangle([38, 41, 40, 47], fill=(255, 255, 255, 240))

        # Paused overlay: two vertical bars
        if paused:
            bar = (200, 60, 60, 220)
            draw.rounded_rectangle([22, 28, 29, 48], radius=2, fill=bar)
            draw.rounded_rectangle([35, 28, 42, 48], radius=2, fill=bar)

        return image

    def _toggle_pause(self, icon, item):
        """Toggle the paused state and update the icon."""
        if self._paused_event.is_set():
            self._paused_event.clear()
            logger.info("Resumed")
        else:
            self._paused_event.set()
            logger.info("Paused")
        icon.icon = self._create_icon_image(self._paused_event.is_set())
        icon.update_menu()

    def _open_settings(self, icon, item):
        """Open the settings dialog in a new thread."""
        from clipboard_typer.settings_dialog import SettingsDialog

        def on_save(new_config: AppConfig, hotkey_changed: bool):
            self._config.start_paused = new_config.start_paused
            self._config.typing.delay_ms = new_config.typing.delay_ms
            self._config.typing.chunk_size = new_config.typing.chunk_size
            self._config.typing.start_delay_ms = new_config.typing.start_delay_ms
            self._config.typing.compensate_indent = new_config.typing.compensate_indent
            self._config.platform.prefer_native = new_config.platform.prefer_native
            if hotkey_changed:
                self._config.hotkey.combo = new_config.hotkey.combo

        dialog = SettingsDialog(self._config, self._config_path, on_save)
        thread = threading.Thread(target=dialog.open, daemon=True)
        thread.start()

    def start(self) -> None:
        try:
            from pystray import Icon, Menu, MenuItem
            from PIL import Image, ImageDraw
        except ImportError:
            logger.info("pystray not installed; running without tray icon. "
                        "Install with: pip install clipboard-typer[tray]")
            return

        self._Image = Image
        self._ImageDraw = ImageDraw

        image = self._create_icon_image(paused=self._paused_event.is_set())

        menu = Menu(
            MenuItem("Clipboard Typer", None, enabled=False),
            Menu.SEPARATOR,
            MenuItem(
                lambda item: "Resume" if self._paused_event.is_set() else "Pause",
                self._toggle_pause,
            ),
            MenuItem("Settings", self._open_settings),
            Menu.SEPARATOR,
            MenuItem("Quit", lambda _icon, _item: self._on_quit()),
        )
        self._icon = Icon("clipboard-typer", image, "Clipboard Typer", menu)

        thread = threading.Thread(target=self._icon.run, daemon=True)
        thread.start()
        logger.debug("Tray icon started")

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()
            logger.debug("Tray icon stopped")
