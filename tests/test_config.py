import os
import tempfile
import pytest
from src.config import load_config, TCPConfig, DEFAULT_CONFIG


class TestLoadConfig:
    def test_returns_defaults_when_no_file(self, tmp_path):
        config = load_config(config_dir=str(tmp_path))
        assert config == DEFAULT_CONFIG

    def test_loads_save_dir_from_file(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text('save_dir = "C:/Screenshots"')
        config = load_config(config_dir=str(tmp_path))
        assert config.save_dir == "C:/Screenshots"

    def test_loads_extra_terminals(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text('extra_terminals = ["hyper.exe", "tabby.exe"]')
        config = load_config(config_dir=str(tmp_path))
        assert config.extra_terminals == ["hyper.exe", "tabby.exe"]

    def test_partial_config_fills_defaults(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text('format = "jpg"')
        config = load_config(config_dir=str(tmp_path))
        assert config.format == "jpg"
        assert config.recency_window == 5
        assert config.path_style == "native"

    def test_unknown_keys_ignored(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text('bogus_key = "whatever"\nformat = "png"')
        config = load_config(config_dir=str(tmp_path))
        assert config.format == "png"


class TestTCPConfig:
    def test_default_config_values(self):
        c = DEFAULT_CONFIG
        assert c.save_dir == ""
        assert c.filename_pattern == "tcp_%Y%m%d_%H%M%S.png"
        assert c.recency_window == 5
        assert c.format == "png"
        assert c.path_style == "native"
        assert c.extra_terminals == []
