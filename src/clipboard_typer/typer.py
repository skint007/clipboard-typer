import logging
import subprocess
import time
from abc import ABC, abstractmethod

from clipboard_typer.platform_detect import OS, DisplayServer, PlatformInfo

logger = logging.getLogger(__name__)


class TyperBackend(ABC):
    @abstractmethod
    def type_text(self, text: str, delay_ms: int, chunk_size: int) -> None:
        """Type the given text."""


class PynputTyper(TyperBackend):
    """Uses pynput.keyboard.Controller for keystroke simulation."""

    def __init__(self):
        from pynput.keyboard import Controller, Key
        self._controller = Controller()
        self._special_keys = {
            "\n": Key.enter,
            "\r": Key.enter,
            "\t": Key.tab,
        }

    def type_text(self, text: str, delay_ms: int, chunk_size: int) -> None:
        delay_s = delay_ms / 1000.0
        for char in text:
            key = self._special_keys.get(char, char)
            self._controller.press(key)
            self._controller.release(key)
            if delay_s > 0:
                time.sleep(delay_s)


class WtypeTyper(TyperBackend):
    """Uses wtype subprocess for Wayland keystroke simulation."""

    def type_text(self, text: str, delay_ms: int, chunk_size: int) -> None:
        cmd = ["wtype", "-d", str(delay_ms), "-"]
        logger.debug("Running: %s (stdin: %d chars)", cmd, len(text))
        subprocess.run(cmd, input=text, text=True, check=True)


class YdotoolTyper(TyperBackend):
    """Uses ydotool for keystroke simulation (works on any Wayland compositor via uinput)."""

    def type_text(self, text: str, delay_ms: int, chunk_size: int) -> None:
        cmd = ["ydotool", "type", "--key-delay", str(delay_ms), "--", text]
        logger.debug("Running: ydotool type (%d chars)", len(text))
        subprocess.run(cmd, check=True)


class XdotoolTyper(TyperBackend):
    """Uses xdotool subprocess for X11 keystroke simulation."""

    def type_text(self, text: str, delay_ms: int, chunk_size: int) -> None:
        cmd = ["xdotool", "type", "--clearmodifiers", "--delay", str(delay_ms),
               "--file", "-"]
        logger.debug("Running: %s (stdin: %d chars)", cmd, len(text))
        subprocess.run(cmd, input=text, text=True, check=True)


class NoBackendError(RuntimeError):
    """Raised when no typing backend is available."""


def select_typer(platform_info: PlatformInfo, prefer_native: bool) -> TyperBackend:
    """Select the best available typing backend for the current platform."""
    # Windows and macOS: pynput works natively
    if platform_info.os in (OS.WINDOWS, OS.MACOS):
        logger.debug("Non-Linux OS, using PynputTyper")
        return PynputTyper()

    # Wayland: pynput cannot simulate keystrokes into native Wayland windows.
    # ydotool works on any compositor (via uinput), wtype needs compositor support.
    if platform_info.display_server == DisplayServer.WAYLAND:
        if platform_info.has_ydotool:
            logger.debug("Wayland detected, using YdotoolTyper")
            return YdotoolTyper()
        if platform_info.has_wtype:
            logger.debug("Wayland detected, using WtypeTyper")
            return WtypeTyper()
        if platform_info.has_xdotool:
            logger.debug("Wayland detected, using XdotoolTyper (XWayland)")
            return XdotoolTyper()
        raise NoBackendError(
            "No typing backend available on Wayland. "
            "Install ydotool: sudo pacman -S ydotool (Arch) or sudo apt install ydotool (Debian)"
        )

    # X11: try pynput first if preferred
    if prefer_native and platform_info.display_server == DisplayServer.X11:
        try:
            backend = PynputTyper()
            logger.debug("X11 + prefer_native=True, using PynputTyper")
            return backend
        except Exception as e:
            logger.debug("PynputTyper unavailable: %s", e)

    # X11 fallbacks
    if platform_info.display_server == DisplayServer.X11:
        if platform_info.has_xdotool:
            logger.debug("X11 detected, using XdotoolTyper")
            return XdotoolTyper()
        raise NoBackendError(
            "No typing backend available on X11. "
            "Install xdotool: sudo pacman -S xdotool (Arch) or sudo apt install xdotool (Debian)"
        )

    raise NoBackendError(
        "No typing backend available. Could not detect display server. "
        "Ensure $DISPLAY or $WAYLAND_DISPLAY is set."
    )
