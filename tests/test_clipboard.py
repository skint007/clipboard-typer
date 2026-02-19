from unittest.mock import patch

import pytest

from clipboard_typer.clipboard import ClipboardError, read_clipboard


class TestReadClipboard:
    @patch("clipboard_typer.clipboard.pyperclip.paste", return_value="hello world")
    def test_returns_clipboard_text(self, mock_paste):
        assert read_clipboard() == "hello world"

    @patch("clipboard_typer.clipboard.pyperclip.paste", return_value="")
    def test_raises_on_empty_clipboard(self, mock_paste):
        with pytest.raises(ClipboardError, match="empty"):
            read_clipboard()

    @patch("clipboard_typer.clipboard.pyperclip.paste", return_value=None)
    def test_raises_on_none_clipboard(self, mock_paste):
        with pytest.raises(ClipboardError, match="empty"):
            read_clipboard()

    @patch("clipboard_typer.clipboard.pyperclip.paste",
           side_effect=Exception("no clipboard tool"))
    def test_raises_on_pyperclip_error(self, mock_paste):
        with pytest.raises(ClipboardError, match="Cannot access clipboard"):
            read_clipboard()
