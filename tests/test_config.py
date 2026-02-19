import textwrap
from pathlib import Path

from clipboard_typer.config import (
    AppConfig,
    HotkeyConfig,
    PlatformConfig,
    TypingConfig,
    load_config,
    save_config,
)


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


class TestSaveConfig:
    def test_roundtrip_defaults(self, tmp_path):
        path = tmp_path / "config.toml"
        save_config(AppConfig(), path)
        loaded = load_config(path)
        assert loaded.hotkey.combo == "ctrl+shift+v"
        assert loaded.typing.delay_ms == 10
        assert loaded.typing.chunk_size == 0
        assert loaded.typing.start_delay_ms == 300
        assert loaded.typing.compensate_indent is False
        assert loaded.platform.prefer_native is True

    def test_roundtrip_custom(self, tmp_path):
        path = tmp_path / "config.toml"
        config = AppConfig(
            hotkey=HotkeyConfig(combo="alt+v"),
            typing=TypingConfig(delay_ms=50, chunk_size=100,
                                start_delay_ms=500, compensate_indent=True),
            platform=PlatformConfig(prefer_native=False),
        )
        save_config(config, path)
        loaded = load_config(path)
        assert loaded.hotkey.combo == "alt+v"
        assert loaded.typing.delay_ms == 50
        assert loaded.typing.chunk_size == 100
        assert loaded.typing.start_delay_ms == 500
        assert loaded.typing.compensate_indent is True
        assert loaded.platform.prefer_native is False

    def test_creates_parent_directories(self, tmp_path):
        path = tmp_path / "subdir" / "nested" / "config.toml"
        save_config(AppConfig(), path)
        assert path.is_file()

    def test_output_is_valid_toml(self, tmp_path):
        import tomllib
        path = tmp_path / "config.toml"
        save_config(AppConfig(), path)
        with open(path, "rb") as f:
            data = tomllib.load(f)
        assert "hotkey" in data
        assert "typing" in data
        assert "platform" in data


class TestLoadConfigDefaultPath:
    def test_uses_xdg_config_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        cfg_dir = tmp_path / "clipboard-typer"
        cfg_dir.mkdir()
        cfg_file = cfg_dir / "config.toml"
        cfg_file.write_text("[typing]\ndelay_ms = 42\n")
        config = load_config()  # no explicit path
        assert config.typing.delay_ms == 42
