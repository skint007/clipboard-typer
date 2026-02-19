import logging
import subprocess
import time
from abc import ABC, abstractmethod

from clipboard_typer.platform_detect import OS, DisplayServer, PlatformInfo

logger = logging.getLogger(__name__)


class TyperBackend(ABC):
    @abstractmethod
    def type_text(self, text: str, delay_ms: int, chunk_size: int,
                  compensate_indent: bool = False) -> None:
        """Type the given text."""


class PynputTyper(TyperBackend):
    """Uses pynput.keyboard.Controller for keystroke simulation."""

    def __init__(self):
        from pynput.keyboard import Controller, Key
        self._controller = Controller()
        self._Key = Key
        self._special_keys = {
            "\n": Key.enter,
            "\r": Key.enter,
            "\t": Key.tab,
        }

    def type_text(self, text: str, delay_ms: int, chunk_size: int,
                  compensate_indent: bool = False) -> None:
        delay_s = delay_ms / 1000.0
        Key = self._Key
        for char in text:
            if char == "\n" and compensate_indent:
                # Enter, then Home + Shift+End to select any auto-indent
                self._controller.press(Key.enter)
                self._controller.release(Key.enter)
                if delay_s > 0:
                    time.sleep(delay_s)
                self._controller.press(Key.home)
                self._controller.release(Key.home)
                self._controller.press(Key.shift)
                self._controller.press(Key.end)
                self._controller.release(Key.end)
                self._controller.release(Key.shift)
            else:
                key = self._special_keys.get(char, char)
                self._controller.press(key)
                self._controller.release(key)
            if delay_s > 0:
                time.sleep(delay_s)


class WtypeTyper(TyperBackend):
    """Uses wtype subprocess for Wayland keystroke simulation."""

    def type_text(self, text: str, delay_ms: int, chunk_size: int,
                  compensate_indent: bool = False) -> None:
        if not compensate_indent:
            cmd = ["wtype", "-d", str(delay_ms), "-"]
            logger.debug("Running: %s (stdin: %d chars)", cmd, len(text))
            subprocess.run(cmd, input=text, text=True, check=True)
        else:
            self._type_with_indent_compensation(text, delay_ms)

    def _type_with_indent_compensation(self, text: str, delay_ms: int) -> None:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if i > 0:
                subprocess.run(["wtype", "-k", "Return"], check=True)
                subprocess.run(["wtype", "-k", "Home"], check=True)
                subprocess.run(
                    ["wtype", "-M", "shift", "-k", "End", "-m", "shift"],
                    check=True,
                )
            if line:
                subprocess.run(
                    ["wtype", "-d", str(delay_ms), "--", line],
                    text=True, check=True,
                )


class YdotoolTyper(TyperBackend):
    """Uses ydotool for keystroke simulation (works on any Wayland compositor via uinput)."""

    # evdev key codes
    _KEY_ENTER = "28:1 28:0"
    _KEY_HOME = "102:1 102:0"
    _KEY_SHIFT_END = "42:1 107:1 107:0 42:0"  # Shift down, End press/release, Shift up

    def type_text(self, text: str, delay_ms: int, chunk_size: int,
                  compensate_indent: bool = False) -> None:
        if not compensate_indent:
            cmd = ["ydotool", "type", "--key-delay", str(delay_ms), "--", text]
            logger.debug("Running: ydotool type (%d chars)", len(text))
            subprocess.run(cmd, check=True)
        else:
            self._type_with_indent_compensation(text, delay_ms)

    def _type_with_indent_compensation(self, text: str, delay_ms: int) -> None:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if i > 0:
                subprocess.run(
                    ["ydotool", "key", *self._KEY_ENTER.split()], check=True
                )
                subprocess.run(
                    ["ydotool", "key", *self._KEY_HOME.split()], check=True
                )
                subprocess.run(
                    ["ydotool", "key", *self._KEY_SHIFT_END.split()], check=True
                )
            if line:
                subprocess.run(
                    ["ydotool", "type", "--key-delay", str(delay_ms), "--", line],
                    check=True,
                )


class XdotoolTyper(TyperBackend):
    """Uses xdotool subprocess for X11 keystroke simulation."""

    def type_text(self, text: str, delay_ms: int, chunk_size: int,
                  compensate_indent: bool = False) -> None:
        if not compensate_indent:
            cmd = ["xdotool", "type", "--clearmodifiers", "--delay", str(delay_ms),
                   "--file", "-"]
            logger.debug("Running: %s (stdin: %d chars)", cmd, len(text))
            subprocess.run(cmd, input=text, text=True, check=True)
        else:
            self._type_with_indent_compensation(text, delay_ms)

    def _type_with_indent_compensation(self, text: str, delay_ms: int) -> None:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if i > 0:
                subprocess.run(["xdotool", "key", "Return"], check=True)
                subprocess.run(["xdotool", "key", "Home"], check=True)
                subprocess.run(["xdotool", "key", "shift+End"], check=True)
            if line:
                subprocess.run(
                    ["xdotool", "type", "--clearmodifiers", "--delay",
                     str(delay_ms), "--file", "-"],
                    input=line, text=True, check=True,
                )


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
