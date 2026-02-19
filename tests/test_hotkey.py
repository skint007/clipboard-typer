import pytest

from clipboard_typer.hotkey import parse_hotkey_combo


class TestParseHotkeyCombo:
    def test_ctrl_shift_v(self):
        assert parse_hotkey_combo("ctrl+shift+v") == "<ctrl>+<shift>+v"

    def test_alt_v(self):
        assert parse_hotkey_combo("alt+v") == "<alt>+v"

    def test_cmd_c(self):
        assert parse_hotkey_combo("cmd+c") == "<cmd>+c"

    def test_super_maps_to_cmd(self):
        assert parse_hotkey_combo("super+v") == "<cmd>+v"

    def test_control_alias(self):
        assert parse_hotkey_combo("control+shift+v") == "<ctrl>+<shift>+v"

    def test_case_insensitive(self):
        assert parse_hotkey_combo("Ctrl+Shift+V") == "<ctrl>+<shift>+v"

    def test_spaces_stripped(self):
        assert parse_hotkey_combo("ctrl + shift + v") == "<ctrl>+<shift>+v"

    def test_single_key(self):
        assert parse_hotkey_combo("v") == "v"

    def test_unknown_key_raises(self):
        with pytest.raises(ValueError, match="Unknown key"):
            parse_hotkey_combo("ctrl+pageup")

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            parse_hotkey_combo("")
