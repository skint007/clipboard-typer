import textwrap
from pathlib import Path

from clipboard_typer.config import AppConfig, load_config


class TestLoadConfigDefaults:
    def test_returns_defaults_when_no_file(self, tmp_path):
        config = load_config(tmp_path / "nonexistent.toml")
        assert config.hotkey.combo == "ctrl+shift+v"
        assert config.typing.delay_ms == 10
        assert config.typing.chunk_size == 0
        assert config.platform.prefer_native is True


class TestLoadConfigFromFile:
    def test_full_config(self, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text(textwrap.dedent("""\
            [hotkey]
            combo = "alt+v"

            [typing]
            delay_ms = 50
            chunk_size = 100

            [platform]
            prefer_native = false
        """))
        config = load_config(cfg_file)
        assert config.hotkey.combo == "alt+v"
        assert config.typing.delay_ms == 50
        assert config.typing.chunk_size == 100
        assert config.platform.prefer_native is False

    def test_partial_config_merges_with_defaults(self, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[typing]\ndelay_ms = 25\n")
        config = load_config(cfg_file)
        assert config.typing.delay_ms == 25
        assert config.hotkey.combo == "ctrl+shift+v"  # default
        assert config.typing.chunk_size == 0  # default

    def test_unknown_keys_ignored(self, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("[typing]\ndelay_ms = 5\nunknown_key = 99\n")
        config = load_config(cfg_file)
        assert config.typing.delay_ms == 5

    def test_wrong_type_uses_default(self, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text('[typing]\ndelay_ms = "fast"\n')
        config = load_config(cfg_file)
        assert config.typing.delay_ms == 10  # falls back to default

    def test_invalid_toml_uses_defaults(self, tmp_path):
        cfg_file = tmp_path / "config.toml"
        cfg_file.write_text("this is not valid toml [[[")
        config = load_config(cfg_file)
        assert config.hotkey.combo == "ctrl+shift+v"


class TestLoadConfigDefaultPath:
    def test_uses_xdg_config_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        cfg_dir = tmp_path / "clipboard-typer"
        cfg_dir.mkdir()
        cfg_file = cfg_dir / "config.toml"
        cfg_file.write_text("[typing]\ndelay_ms = 42\n")
        config = load_config()  # no explicit path
        assert config.typing.delay_ms == 42
