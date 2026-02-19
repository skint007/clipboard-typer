import argparse
import logging
import signal
import threading
import time
from pathlib import Path

from clipboard_typer.clipboard import ClipboardError, read_clipboard
from clipboard_typer.config import load_config
from clipboard_typer.hotkey import HotkeyListener
from clipboard_typer.platform_detect import detect_platform
from clipboard_typer.typer import select_typer

logger = logging.getLogger(__name__)


def on_hotkey_triggered(typer_backend, typing_config, paused_event):
    """Called when the global hotkey is pressed."""
    if paused_event.is_set():
        logger.debug("Hotkey pressed but typing is paused; ignoring.")
        return

    try:
        text = read_clipboard()
    except ClipboardError as e:
        logger.warning("Clipboard error: %s", e)
        return

    logger.info("Clipboard contents (%d chars): %r", len(text), text)

    # Wait for modifier keys to be released before typing
    delay = typing_config.start_delay_ms / 1000.0
    logger.debug("Waiting %.0fms for modifier release", typing_config.start_delay_ms)
    time.sleep(delay)

    try:
        typer_backend.type_text(text, typing_config.delay_ms, typing_config.chunk_size,
                               typing_config.compensate_indent)
        logger.info("Finished typing %d characters.", len(text))
    except Exception:
        logger.exception("Typing failed")


def main():
    parser = argparse.ArgumentParser(description="Clipboard Typer")
    parser.add_argument("--config", type=Path, help="Path to config TOML file")
    parser.add_argument("--no-tray", action="store_true", help="Disable system tray icon")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = load_config(args.config)
    platform_info = detect_platform()
    logger.info("Platform: %s, display: %s", platform_info.os.name, platform_info.display_server.name)

    typer_backend = select_typer(platform_info, config.platform.prefer_native)
    logger.info("Using typing backend: %s", type(typer_backend).__name__)

    shutdown_event = threading.Event()
    paused_event = threading.Event()

    def handle_shutdown(*_):
        logger.info("Shutting down...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    callback = lambda: on_hotkey_triggered(typer_backend, config.typing, paused_event)
    listener = HotkeyListener(config.hotkey, callback)
    listener.start()
    logger.info("Listening for hotkey: %s", config.hotkey.combo)

    tray = None
    if not args.no_tray:
        from clipboard_typer.tray import TrayIcon
        tray = TrayIcon(on_quit=handle_shutdown, paused_event=paused_event)
        tray.start()

    try:
        shutdown_event.wait()
    finally:
        listener.stop()
        if tray:
            tray.stop()
        logger.info("Goodbye.")
