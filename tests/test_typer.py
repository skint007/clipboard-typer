from unittest.mock import MagicMock, call, patch

import pytest

from clipboard_typer.platform_detect import OS, DisplayServer, PlatformInfo
from clipboard_typer.typer import (
    NoBackendError,
    PynputTyper,
    WtypeTyper,
    XdotoolTyper,
    YdotoolTyper,
    select_typer,
)


def _make_platform(os=OS.LINUX, ds=DisplayServer.X11, ydotool=False, wtype=False, xdotool=False):
    return PlatformInfo(os=os, display_server=ds, has_ydotool=ydotool, has_wtype=wtype, has_xdotool=xdotool)


class TestPynputTyper:
    @patch("clipboard_typer.typer.time.sleep")
    def test_types_each_character(self, mock_sleep):
        mock_controller = MagicMock()
        with patch("pynput.keyboard.Controller", return_value=mock_controller):
            with patch("pynput.keyboard.Key") as mock_key:
                typer = PynputTyper()

        typer.type_text("ab", delay_ms=10, chunk_size=0)
        assert mock_controller.press.call_count == 2
        mock_controller.press.assert_any_call("a")
        mock_controller.press.assert_any_call("b")
        assert mock_controller.release.call_count == 2
        assert mock_sleep.call_count == 2

    @patch("clipboard_typer.typer.time.sleep")
    def test_handles_newline(self, mock_sleep):
        mock_controller = MagicMock()
        with patch("pynput.keyboard.Controller", return_value=mock_controller):
            with patch("pynput.keyboard.Key") as mock_key:
                mock_key.enter = "ENTER"
                typer = PynputTyper()
                typer._special_keys["\n"] = mock_key.enter

        typer.type_text("\n", delay_ms=0, chunk_size=0)
        mock_controller.press.assert_called_once_with("ENTER")
        mock_controller.release.assert_called_once_with("ENTER")

    @patch("clipboard_typer.typer.time.sleep")
    def test_no_sleep_when_delay_zero(self, mock_sleep):
        mock_controller = MagicMock()
        with patch("pynput.keyboard.Controller", return_value=mock_controller):
            with patch("pynput.keyboard.Key"):
                typer = PynputTyper()

        typer.type_text("a", delay_ms=0, chunk_size=0)
        mock_sleep.assert_not_called()


class TestPynputTyperCompensateIndent:
    @patch("clipboard_typer.typer.time.sleep")
    def test_newline_sends_home_shift_end(self, mock_sleep):
        mock_controller = MagicMock()
        with patch("pynput.keyboard.Controller", return_value=mock_controller):
            with patch("pynput.keyboard.Key") as mock_key:
                mock_key.enter = "ENTER"
                mock_key.home = "HOME"
                mock_key.shift = "SHIFT"
                mock_key.end = "END"
                typer = PynputTyper()
                typer._special_keys["\n"] = mock_key.enter

        typer.type_text("a\nb", delay_ms=0, chunk_size=0, compensate_indent=True)
        calls = mock_controller.press.call_args_list
        # a, Enter, Home, Shift, End, b
        assert calls[0] == call("a")
        assert calls[1] == call("ENTER")
        assert calls[2] == call("HOME")
        assert calls[3] == call("SHIFT")
        assert calls[4] == call("END")
        assert calls[5] == call("b")


class TestWtypeTyper:
    @patch("clipboard_typer.typer.subprocess.run")
    def test_runs_wtype_command(self, mock_run):
        typer = WtypeTyper()
        typer.type_text("hello", delay_ms=10, chunk_size=0)
        mock_run.assert_called_once_with(
            ["wtype", "-d", "10", "-"],
            input="hello", text=True, check=True,
        )


class TestWtypeTyperCompensateIndent:
    @patch("clipboard_typer.typer.subprocess.run")
    def test_splits_lines_with_key_commands(self, mock_run):
        typer = WtypeTyper()
        typer.type_text("a\nb", delay_ms=10, chunk_size=0, compensate_indent=True)
        # line "a" (1), Return (1), Home (1), Shift+End (1), line "b" (1) = 5
        assert mock_run.call_count == 5


class TestYdotoolTyper:
    @patch("clipboard_typer.typer.subprocess.run")
    def test_runs_ydotool_command(self, mock_run):
        typer = YdotoolTyper()
        typer.type_text("hello", delay_ms=10, chunk_size=0)
        mock_run.assert_called_once_with(
            ["ydotool", "type", "--key-delay", "10", "--", "hello"],
            check=True,
        )


class TestYdotoolTyperCompensateIndent:
    @patch("clipboard_typer.typer.subprocess.run")
    def test_splits_lines_with_key_commands(self, mock_run):
        typer = YdotoolTyper()
        typer.type_text("a\nb", delay_ms=10, chunk_size=0, compensate_indent=True)
        # line "a" (1), Enter key (1), Home key (1), Shift+End key (1), line "b" (1) = 5
        assert mock_run.call_count == 5


class TestXdotoolTyper:
    @patch("clipboard_typer.typer.subprocess.run")
    def test_runs_xdotool_command(self, mock_run):
        typer = XdotoolTyper()
        typer.type_text("hello", delay_ms=10, chunk_size=0)
        mock_run.assert_called_once_with(
            ["xdotool", "type", "--clearmodifiers", "--delay", "10", "--file", "-"],
            input="hello", text=True, check=True,
        )


class TestXdotoolTyperCompensateIndent:
    @patch("clipboard_typer.typer.subprocess.run")
    def test_splits_lines_with_key_commands(self, mock_run):
        typer = XdotoolTyper()
        typer.type_text("a\nb", delay_ms=10, chunk_size=0, compensate_indent=True)
        # line "a" (1), Return key (1), Home key (1), shift+End key (1), line "b" (1) = 5
        assert mock_run.call_count == 5


class TestSelectTyper:
    def test_windows_uses_pynput(self):
        p = _make_platform(os=OS.WINDOWS, ds=DisplayServer.NONE)
        with patch("pynput.keyboard.Controller"):
            with patch("pynput.keyboard.Key"):
                backend = select_typer(p, prefer_native=True)
        assert isinstance(backend, PynputTyper)

    def test_macos_uses_pynput(self):
        p = _make_platform(os=OS.MACOS, ds=DisplayServer.NONE)
        with patch("pynput.keyboard.Controller"):
            with patch("pynput.keyboard.Key"):
                backend = select_typer(p, prefer_native=True)
        assert isinstance(backend, PynputTyper)

    def test_linux_prefer_native_uses_pynput(self):
        p = _make_platform(os=OS.LINUX, ds=DisplayServer.X11)
        with patch("pynput.keyboard.Controller"):
            with patch("pynput.keyboard.Key"):
                backend = select_typer(p, prefer_native=True)
        assert isinstance(backend, PynputTyper)

    def test_linux_wayland_uses_ydotool(self):
        p = _make_platform(os=OS.LINUX, ds=DisplayServer.WAYLAND, ydotool=True)
        backend = select_typer(p, prefer_native=False)
        assert isinstance(backend, YdotoolTyper)

    def test_linux_wayland_uses_ydotool_even_with_prefer_native(self):
        p = _make_platform(os=OS.LINUX, ds=DisplayServer.WAYLAND, ydotool=True)
        backend = select_typer(p, prefer_native=True)
        assert isinstance(backend, YdotoolTyper)

    def test_linux_wayland_falls_back_to_wtype(self):
        p = _make_platform(os=OS.LINUX, ds=DisplayServer.WAYLAND, wtype=True)
        backend = select_typer(p, prefer_native=False)
        assert isinstance(backend, WtypeTyper)

    def test_linux_wayland_falls_back_to_xdotool(self):
        p = _make_platform(os=OS.LINUX, ds=DisplayServer.WAYLAND, xdotool=True)
        backend = select_typer(p, prefer_native=False)
        assert isinstance(backend, XdotoolTyper)

    def test_linux_x11_uses_xdotool(self):
        p = _make_platform(os=OS.LINUX, ds=DisplayServer.X11, xdotool=True)
        backend = select_typer(p, prefer_native=False)
        assert isinstance(backend, XdotoolTyper)

    def test_linux_wayland_no_tools_raises(self):
        p = _make_platform(os=OS.LINUX, ds=DisplayServer.WAYLAND)
        with pytest.raises(NoBackendError, match="ydotool"):
            select_typer(p, prefer_native=False)

    def test_linux_x11_no_tools_raises(self):
        p = _make_platform(os=OS.LINUX, ds=DisplayServer.X11)
        with pytest.raises(NoBackendError, match="xdotool"):
            select_typer(p, prefer_native=False)

    def test_linux_no_display_server_raises(self):
        p = _make_platform(os=OS.LINUX, ds=DisplayServer.NONE)
        with pytest.raises(NoBackendError, match="display server"):
            select_typer(p, prefer_native=False)
