import logging
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable

from clipboard_typer.config import (
    AppConfig,
    load_config,
    save_config,
)

logger = logging.getLogger(__name__)

_dialog_lock = threading.Lock()

_QSS_PATH = Path(__file__).parent / "resources" / "style.qss"


class SettingsDialog:
    """Opens the settings dialog in a subprocess so Qt gets its own main thread."""

    def __init__(self, config: AppConfig, config_path: Path,
                 on_save: Callable[[AppConfig, bool], None]):
        self._config = config
        self._config_path = config_path
        self._on_save = on_save

    def open(self) -> None:
        if not _dialog_lock.acquire(blocking=False):
            logger.debug("Settings dialog already open")
            return
        try:
            self._run_subprocess()
        except Exception:
            logger.exception("Failed to open settings dialog")
        finally:
            _dialog_lock.release()

    def _run_subprocess(self) -> None:
        # Save current config so the subprocess can read it
        save_config(self._config, self._config_path)

        result = subprocess.run(
            [sys.executable, "-m", "clipboard_typer.settings_dialog",
             str(self._config_path)],
        )

        if result.returncode == 0:
            old_combo = self._config.hotkey.combo
            new_config = load_config(self._config_path)
            hotkey_changed = new_config.hotkey.combo != old_combo
            self._on_save(new_config, hotkey_changed)


# ---------------------------------------------------------------------------
# Everything below runs only in the subprocess (python -m clipboard_typer.settings_dialog)
# ---------------------------------------------------------------------------

def _build_and_run(config_path: Path) -> int:
    """Build and show the Qt dialog. Returns 0 on save, 1 on cancel."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import (
        QApplication,
        QCheckBox,
        QDialog,
        QDialogButtonBox,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QSlider,
        QVBoxLayout,
    )

    from clipboard_typer.config import (
        AppConfig,
        HotkeyConfig,
        PlatformConfig,
        TypingConfig,
        load_config,
        save_config,
    )

    config = load_config(config_path)

    app = QApplication([])
    app.setStyle("Fusion")
    if _QSS_PATH.is_file():
        app.setStyleSheet(_QSS_PATH.read_text(encoding="utf-8"))

    dialog = QDialog()
    dialog.setWindowTitle("Clipboard Typer Settings")
    dialog.setMinimumWidth(400)
    layout = QVBoxLayout(dialog)

    # --- General ---
    general_group = QGroupBox("General")
    general_layout = QVBoxLayout(general_group)

    start_paused_cb = QCheckBox("Start paused")
    start_paused_cb.setChecked(config.start_paused)
    general_layout.addWidget(start_paused_cb)

    layout.addWidget(general_group)

    # --- Hotkey ---
    hotkey_group = QGroupBox("Hotkey")
    hotkey_layout = QHBoxLayout(hotkey_group)

    hotkey_layout.addWidget(QLabel("Combo"))
    combo_edit = QLineEdit(config.hotkey.combo)
    hotkey_layout.addWidget(combo_edit)

    layout.addWidget(hotkey_group)

    # --- Typing ---
    typing_group = QGroupBox("Typing")
    typing_layout = QVBoxLayout(typing_group)

    delay_slider = _add_slider_row(
        typing_layout, "Delay (ms)", config.typing.delay_ms, 0, 200)
    chunk_slider = _add_slider_row(
        typing_layout, "Chunk size", config.typing.chunk_size, 0, 500)
    start_delay_slider = _add_slider_row(
        typing_layout, "Start delay (ms)", config.typing.start_delay_ms, 0, 1000)

    compensate_cb = QCheckBox("Compensate auto-indent")
    compensate_cb.setChecked(config.typing.compensate_indent)
    typing_layout.addWidget(compensate_cb)

    layout.addWidget(typing_group)

    # --- Platform ---
    platform_group = QGroupBox("Platform")
    platform_layout = QVBoxLayout(platform_group)

    prefer_native_cb = QCheckBox("Prefer native backend (pynput)")
    prefer_native_cb.setChecked(config.platform.prefer_native)
    platform_layout.addWidget(prefer_native_cb)

    layout.addWidget(platform_group)

    # --- Buttons ---
    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Save
        | QDialogButtonBox.StandardButton.Cancel
    )
    saved = False

    def on_save():
        nonlocal saved
        new_config = AppConfig(
            start_paused=start_paused_cb.isChecked(),
            hotkey=HotkeyConfig(combo=combo_edit.text().strip()),
            typing=TypingConfig(
                delay_ms=delay_slider.value(),
                chunk_size=chunk_slider.value(),
                start_delay_ms=start_delay_slider.value(),
                compensate_indent=compensate_cb.isChecked(),
            ),
            platform=PlatformConfig(
                prefer_native=prefer_native_cb.isChecked()),
        )

        try:
            save_config(new_config, config_path)
        except OSError as e:
            QMessageBox.critical(dialog, "Save failed",
                                 f"Could not write config: {e}")
            return

        if new_config.hotkey.combo != config.hotkey.combo:
            QMessageBox.information(
                dialog, "Restart required",
                "Hotkey changed. Restart the service for it to take "
                "effect:\n\nsystemctl --user restart clipboard-typer",
            )

        saved = True
        dialog.accept()

    buttons.accepted.connect(on_save)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    dialog.exec()
    app.quit()
    return 0 if saved else 1


def _add_slider_row(parent_layout, label_text: str, value: int,
                    min_val: int, max_val: int):
    """Add a labeled slider row and return the slider widget."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QSlider

    row = QHBoxLayout()

    label = QLabel(label_text)
    label.setMinimumWidth(110)
    row.addWidget(label)

    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setRange(min_val, max_val)
    slider.setValue(value)
    row.addWidget(slider)

    value_label = QLabel(str(value))
    value_label.setMinimumWidth(35)
    value_label.setAlignment(Qt.AlignmentFlag.AlignRight
                             | Qt.AlignmentFlag.AlignVCenter)
    row.addWidget(value_label)

    slider.valueChanged.connect(lambda v: value_label.setText(str(v)))

    parent_layout.addLayout(row)
    return slider


if __name__ == "__main__":
    sys.exit(_build_and_run(Path(sys.argv[1])))
