from unittest.mock import patch

from clipboard_typer.settings_dialog import _validate_int


class TestValidateInt:
    @patch("clipboard_typer.settings_dialog.messagebox")
    def test_valid_integer(self, mock_msgbox):
        assert _validate_int("Test", "42") == 42
        mock_msgbox.showerror.assert_not_called()

    @patch("clipboard_typer.settings_dialog.messagebox")
    def test_zero_is_valid(self, mock_msgbox):
        assert _validate_int("Test", "0") == 0

    @patch("clipboard_typer.settings_dialog.messagebox")
    def test_non_integer_returns_none(self, mock_msgbox):
        assert _validate_int("Test", "abc") is None
        mock_msgbox.showerror.assert_called_once()

    @patch("clipboard_typer.settings_dialog.messagebox")
    def test_negative_returns_none(self, mock_msgbox):
        assert _validate_int("Test", "-1") is None
        mock_msgbox.showerror.assert_called_once()

    @patch("clipboard_typer.settings_dialog.messagebox")
    def test_float_returns_none(self, mock_msgbox):
        assert _validate_int("Test", "1.5") is None
        mock_msgbox.showerror.assert_called_once()

    @patch("clipboard_typer.settings_dialog.messagebox")
    def test_empty_returns_none(self, mock_msgbox):
        assert _validate_int("Test", "") is None
        mock_msgbox.showerror.assert_called_once()
