import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)


class TrayIcon:
    def __init__(self, on_quit: Callable[[], None], paused_event: threading.Event):
        self._on_quit = on_quit
        self._paused_event = paused_event
        self._icon = None
        self._Image = None
        self._ImageDraw = None

    def _create_icon_image(self, paused: bool):
        """Create the tray icon image with visual state indication."""
        if paused:
            image = self._Image.new("RGB", (64, 64), color=(60, 20, 20))
            draw = self._ImageDraw.Draw(image)
            draw.text((12, 16), "CT", fill=(120, 120, 120))
        else:
            image = self._Image.new("RGB", (64, 64), color=(30, 30, 30))
            draw = self._ImageDraw.Draw(image)
            draw.text((12, 16), "CT", fill=(0, 180, 255))
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

        image = self._create_icon_image(paused=False)

        menu = Menu(
            MenuItem("Clipboard Typer", None, enabled=False),
            Menu.SEPARATOR,
            MenuItem(
                lambda item: "Resume" if self._paused_event.is_set() else "Pause",
                self._toggle_pause,
            ),
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
