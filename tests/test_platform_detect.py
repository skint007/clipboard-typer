from unittest.mock import patch

from clipboard_typer.platform_detect import (
    OS,
    DisplayServer,
    PlatformInfo,
    detect_platform,
)


def _mock_detect(system="Linux", env=None, which_map=None):
    env = env or {}
    which_map = which_map or {}

    def fake_which(name):
        return which_map.get(name)

    with (
        patch("clipboard_typer.platform_detect.platform.system", return_value=system),
        patch.dict("os.environ", env, clear=True),
        patch("clipboard_typer.platform_detect.shutil.which", side_effect=fake_which),
    ):
        return detect_platform()


class TestDetectOS:
    def test_linux(self):
        info = _mock_detect(system="Linux")
        assert info.os == OS.LINUX

    def test_windows(self):
        info = _mock_detect(system="Windows")
        assert info.os == OS.WINDOWS

    def test_macos(self):
        info = _mock_detect(system="Darwin")
        assert info.os == OS.MACOS

    def test_unknown_defaults_to_linux(self):
        info = _mock_detect(system="FreeBSD")
        assert info.os == OS.LINUX


class TestDetectDisplayServer:
    def test_wayland_via_session_type(self):
        info = _mock_detect(env={"XDG_SESSION_TYPE": "wayland"})
        assert info.display_server == DisplayServer.WAYLAND

    def test_wayland_via_wayland_display(self):
        info = _mock_detect(env={"WAYLAND_DISPLAY": "wayland-0"})
        assert info.display_server == DisplayServer.WAYLAND

    def test_x11_via_session_type(self):
        info = _mock_detect(env={"XDG_SESSION_TYPE": "x11"})
        assert info.display_server == DisplayServer.X11

    def test_x11_via_display(self):
        info = _mock_detect(env={"DISPLAY": ":0"})
        assert info.display_server == DisplayServer.X11

    def test_none_when_no_env(self):
        info = _mock_detect()
        assert info.display_server == DisplayServer.NONE

    def test_non_linux_always_none(self):
        info = _mock_detect(system="Windows", env={"DISPLAY": ":0"})
        assert info.display_server == DisplayServer.NONE


class TestDetectTools:
    def test_has_ydotool(self):
        info = _mock_detect(which_map={"ydotool": "/usr/bin/ydotool"})
        assert info.has_ydotool is True
        assert info.has_wtype is False
        assert info.has_xdotool is False

    def test_has_wtype(self):
        info = _mock_detect(which_map={"wtype": "/usr/bin/wtype"})
        assert info.has_ydotool is False
        assert info.has_wtype is True
        assert info.has_xdotool is False

    def test_has_xdotool(self):
        info = _mock_detect(which_map={"xdotool": "/usr/bin/xdotool"})
        assert info.has_wtype is False
        assert info.has_xdotool is True

    def test_has_all(self):
        info = _mock_detect(which_map={
            "ydotool": "/usr/bin/ydotool",
            "wtype": "/usr/bin/wtype",
            "xdotool": "/usr/bin/xdotool",
        })
        assert info.has_ydotool is True
        assert info.has_wtype is True
        assert info.has_xdotool is True

    def test_has_none(self):
        info = _mock_detect()
        assert info.has_ydotool is False
        assert info.has_wtype is False
        assert info.has_xdotool is False


class TestPlatformInfoFrozen:
    def test_immutable(self):
        info = _mock_detect()
        try:
            info.os = OS.WINDOWS
            assert False, "Should have raised"
        except AttributeError:
            pass
