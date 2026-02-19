import logging
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class HotkeyConfig:
    combo: str = "ctrl+shift+v"


@dataclass
class TypingConfig:
    delay_ms: int = 10
    chunk_size: int = 0  # 0 = type everything at once
    start_delay_ms: int = 300  # delay before typing to let modifier keys be released


@dataclass
class PlatformConfig:
    prefer_native: bool = True


@dataclass
class AppConfig:
    hotkey: HotkeyConfig = field(default_factory=HotkeyConfig)
    typing: TypingConfig = field(default_factory=TypingConfig)
    platform: PlatformConfig = field(default_factory=PlatformConfig)


def _default_config_path() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME", "")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "clipboard-typer" / "config.toml"


def _safe_get(data: dict, key: str, expected_type: type, default):
    """Get a value from a dict, returning default if missing or wrong type."""
    if key not in data:
        return default
    val = data[key]
    if not isinstance(val, expected_type):
        logger.warning("Config key %r: expected %s, got %s; using default %r",
                       key, expected_type.__name__, type(val).__name__, default)
        return default
    return val


def load_config(path: Path | None = None) -> AppConfig:
    """Load config from TOML file, falling back to defaults."""
    config = AppConfig()

    if path is None:
        path = _default_config_path()

    if not path.is_file():
        logger.debug("No config file at %s, using defaults", path)
        return config

    logger.info("Loading config from %s", path)
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        logger.warning("Failed to read config %s: %s; using defaults", path, e)
        return config

    if "hotkey" in data:
        h = data["hotkey"]
        config.hotkey.combo = _safe_get(h, "combo", str, config.hotkey.combo)

    if "typing" in data:
        t = data["typing"]
        config.typing.delay_ms = _safe_get(t, "delay_ms", int, config.typing.delay_ms)
        config.typing.chunk_size = _safe_get(t, "chunk_size", int, config.typing.chunk_size)
        config.typing.start_delay_ms = _safe_get(t, "start_delay_ms", int, config.typing.start_delay_ms)

    if "platform" in data:
        p = data["platform"]
        config.platform.prefer_native = _safe_get(p, "prefer_native", bool,
                                                   config.platform.prefer_native)

    return config
