import logging
from typing import Callable

from clipboard_typer.config import HotkeyConfig

logger = logging.getLogger(__name__)

# Map human-readable modifier names to pynput hotkey format
_MODIFIER_MAP = {
    "ctrl": "<ctrl>",
    "control": "<ctrl>",
    "shift": "<shift>",
    "alt": "<alt>",
    "cmd": "<cmd>",
    "super": "<cmd>",
    "command": "<cmd>",
}


def parse_hotkey_combo(combo_str: str) -> str:
    """Parse 'ctrl+shift+v' into pynput hotkey string '<ctrl>+<shift>+v'."""
    parts = [p.strip().lower() for p in combo_str.split("+")]
    if not parts:
        raise ValueError(f"Empty hotkey combo: {combo_str!r}")

    converted = []
    for part in parts:
        if part in _MODIFIER_MAP:
            converted.append(_MODIFIER_MAP[part])
        elif len(part) == 1:
            converted.append(part)
        else:
            raise ValueError(f"Unknown key in hotkey combo: {part!r}")

    return "+".join(converted)


class HotkeyListener:
    def __init__(self, config: HotkeyConfig, callback: Callable[[], None]):
        self._config = config
        self._callback = callback
        self._listener = None

    def start(self) -> None:
        """Start listening for the global hotkey in a daemon thread."""
        from pynput import keyboard

        hotkey_str = parse_hotkey_combo(self._config.combo)
        logger.debug("Parsed hotkey: %r -> %r", self._config.combo, hotkey_str)

        self._listener = keyboard.GlobalHotKeys({hotkey_str: self._callback})
        self._listener.daemon = True
        self._listener.start()
        logger.info("Hotkey listener started for: %s", self._config.combo)

    def stop(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener.join(timeout=2)
            logger.debug("Hotkey listener stopped")
