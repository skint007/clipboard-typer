import threading
from unittest.mock import MagicMock, patch

from clipboard_typer.app import on_hotkey_triggered
from clipboard_typer.config import TypingConfig


class TestOnHotkeyTriggered:
    def test_skips_when_paused(self):
        paused = threading.Event()
        paused.set()
        mock_typer = MagicMock()

        on_hotkey_triggered(mock_typer, TypingConfig(), paused)

        mock_typer.type_text.assert_not_called()

    def test_types_when_not_paused(self):
        paused = threading.Event()
        mock_typer = MagicMock()

        with patch("clipboard_typer.app.read_clipboard", return_value="hello"):
            with patch("clipboard_typer.app.time.sleep"):
                on_hotkey_triggered(mock_typer, TypingConfig(), paused)

        mock_typer.type_text.assert_called_once_with("hello", 10, 0, False)

    def test_passes_compensate_indent(self):
        paused = threading.Event()
        mock_typer = MagicMock()
        config = TypingConfig(compensate_indent=True)

        with patch("clipboard_typer.app.read_clipboard", return_value="hello"):
            with patch("clipboard_typer.app.time.sleep"):
                on_hotkey_triggered(mock_typer, config, paused)

        mock_typer.type_text.assert_called_once_with("hello", 10, 0, True)

    def test_skips_on_empty_clipboard(self):
        paused = threading.Event()
        mock_typer = MagicMock()

        with patch("clipboard_typer.app.read_clipboard", return_value=""):
            with patch("clipboard_typer.app.time.sleep"):
                on_hotkey_triggered(mock_typer, TypingConfig(), paused)

        mock_typer.type_text.assert_called_once_with("", 10, 0, False)
