import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)


class TrayIcon:
    def __init__(self, on_quit: Callable[[], None]):
        self._on_quit = on_quit
        self._icon = None

    def start(self) -> None:
        try:
            from pystray import Icon, Menu, MenuItem
            from PIL import Image, ImageDraw
        except ImportError:
            logger.info("pystray not installed; running without tray icon. "
                        "Install with: pip install clipboard-typer[tray]")
            return

        image = Image.new("RGB", (64, 64), color=(30, 30, 30))
        draw = ImageDraw.Draw(image)
        draw.text((12, 16), "CT", fill=(0, 180, 255))

        menu = Menu(
            MenuItem("Clipboard Typer", None, enabled=False),
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
