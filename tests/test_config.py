"""Unit tests for configuration loading."""

from pathlib import Path

import pytest

from videos.common import DEFAULT_MAX_HEIGHT
from videos.videos import load_config


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_basic(self, tmp_path: Path):
        """Test loading a basic configuration file."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
link = "https://youtube.com/playlist"
target_folder = "downloads"
"""
        )

        config = load_config(config_file)
        assert config["link"] == "https://youtube.com/playlist"
        assert config["target_folder"] == "downloads"

    def test_load_config_defaults_max_height(self, tmp_path: Path):
        """Test that max_height defaults to DEFAULT_MAX_HEIGHT."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
link = "https://youtube.com/playlist"
target_folder = "downloads"
"""
        )

        config = load_config(config_file)
        assert config["max_height"] == DEFAULT_MAX_HEIGHT

    def test_load_config_defaults_last_download_index(self, tmp_path: Path):
        """Test that last_download_index defaults to 0."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
link = "https://youtube.com/playlist"
target_folder = "downloads"
"""
        )

        config = load_config(config_file)
        assert config["last_download_index"] == 0

    def test_load_config_custom_max_height(self, tmp_path: Path):
        """Test loading config with custom max_height."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
link = "https://youtube.com/playlist"
target_folder = "downloads"
max_height = 720
"""
        )

        config = load_config(config_file)
        assert config["max_height"] == 720

    def test_load_config_custom_last_download_index(self, tmp_path: Path):
        """Test loading config with custom last_download_index."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
link = "https://youtube.com/playlist"
target_folder = "downloads"
last_download_index = 42
"""
        )

        config = load_config(config_file)
        assert config["last_download_index"] == 42

    def test_load_config_missing_link(self, tmp_path: Path):
        """Test that missing link raises ValueError."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
target_folder = "downloads"
"""
        )

        with pytest.raises(
            ValueError, match="Missing required configuration key: link"
        ):
            load_config(config_file)

    def test_load_config_missing_target_folder(self, tmp_path: Path):
        """Test that missing target_folder raises ValueError."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
link = "https://youtube.com/playlist"
"""
        )

        with pytest.raises(
            ValueError, match="Missing required configuration key: target_folder"
        ):
            load_config(config_file)

    def test_load_config_empty_file(self, tmp_path: Path):
        """Test loading an empty config file (no validation needed)."""
        config_file = tmp_path / "config.toml"
        config_file.write_text("")

        # Empty file should load without error (no link/target_folder to validate)
        config = load_config(config_file)
        assert config["max_height"] == DEFAULT_MAX_HEIGHT
        assert config["last_download_index"] == 0

    def test_load_config_with_last_video(self, tmp_path: Path):
        """Test loading config with last_video field."""
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            """
link = "https://youtube.com/playlist"
target_folder = "downloads"
last_video = "abc123"
"""
        )

        config = load_config(config_file)
        assert config["last_video"] == "abc123"

    def test_load_config_file_not_found(self, tmp_path: Path):
        """Test that missing file raises FileNotFoundError."""
        config_file = tmp_path / "nonexistent.toml"

        with pytest.raises(FileNotFoundError):
            load_config(config_file)
