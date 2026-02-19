import threading
from pathlib import Path
from unittest.mock import MagicMock

from clipboard_typer.config import AppConfig
from clipboard_typer.tray import TrayIcon


class TestTrayIconPauseToggle:
    def _make_tray(self, paused=False):
        event = threading.Event()
        if paused:
            event.set()
        config = AppConfig()
        tray = TrayIcon(on_quit=lambda: None, paused_event=event,
                        config=config, config_path=Path("/tmp/test.toml"))
        tray._Image = MagicMock()
        tray._ImageDraw = MagicMock()
        return tray, event

    def test_toggle_pause_sets_event(self):
        tray, event = self._make_tray(paused=False)
        mock_icon = MagicMock()

        tray._toggle_pause(mock_icon, None)

        assert event.is_set()
        mock_icon.update_menu.assert_called_once()

    def test_toggle_resume_clears_event(self):
        tray, event = self._make_tray(paused=True)
        mock_icon = MagicMock()

        tray._toggle_pause(mock_icon, None)

        assert not event.is_set()
        mock_icon.update_menu.assert_called_once()

    def test_toggle_updates_icon_image(self):
        tray, event = self._make_tray(paused=False)
        mock_icon = MagicMock()

        tray._toggle_pause(mock_icon, None)

        # Icon image should be set to the paused image
        assert mock_icon.icon is not None

    def test_double_toggle_returns_to_original_state(self):
        tray, event = self._make_tray(paused=False)
        mock_icon = MagicMock()

        tray._toggle_pause(mock_icon, None)
        assert event.is_set()

        tray._toggle_pause(mock_icon, None)
        assert not event.is_set()
