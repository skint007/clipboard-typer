import logging
import os
import platform
import shutil
from dataclasses import dataclass
from enum import Enum, auto

logger = logging.getLogger(__name__)


class OS(Enum):
    LINUX = auto()
    WINDOWS = auto()
    MACOS = auto()


class DisplayServer(Enum):
    X11 = auto()
    WAYLAND = auto()
    NONE = auto()


@dataclass(frozen=True)
class PlatformInfo:
    os: OS
    display_server: DisplayServer
    has_ydotool: bool
    has_wtype: bool
    has_xdotool: bool


def detect_platform() -> PlatformInfo:
    """Detect OS, display server, and available external tools."""
    system = platform.system()
    if system == "Linux":
        current_os = OS.LINUX
    elif system == "Windows":
        current_os = OS.WINDOWS
    elif system == "Darwin":
        current_os = OS.MACOS
    else:
        logger.warning("Unknown OS %r, assuming Linux", system)
        current_os = OS.LINUX

    display_server = DisplayServer.NONE
    if current_os == OS.LINUX:
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session_type == "wayland" or os.environ.get("WAYLAND_DISPLAY"):
            display_server = DisplayServer.WAYLAND
        elif session_type == "x11" or os.environ.get("DISPLAY"):
            display_server = DisplayServer.X11

    has_ydotool = shutil.which("ydotool") is not None
    has_wtype = shutil.which("wtype") is not None
    has_xdotool = shutil.which("xdotool") is not None

    info = PlatformInfo(
        os=current_os,
        display_server=display_server,
        has_ydotool=has_ydotool,
        has_wtype=has_wtype,
        has_xdotool=has_xdotool,
    )
    logger.debug("Detected platform: %s", info)
    return info
