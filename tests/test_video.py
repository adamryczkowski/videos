"""Unit tests for the Video class."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from videos import Video
from videos.common import LINK_FILE_EXTENSION


class TestVideoCreation:
    """Tests for Video class instantiation."""

    def test_video_from_dict(self):
        """Test creating a Video from a dictionary."""
        entry = {
            "id": "abc123",
            "title": "Test Video",
            "url": "https://example.com/video",
            "duration": 120.5,
            "my_index": 0,
            "my_title": "Test Channel",
        }
        video = Video(entry)
        assert video.id == "abc123"
        assert video.title == "Test Video"
        assert video.url == "https://example.com/video"
        assert video.duration == 120.5
        assert video.index == 0
        assert video.channel_name == "Test Channel"

    def test_video_max_height_default(self):
        """Test that max_height defaults to 1080 when not set."""
        entry = {
            "id": "abc123",
            "title": "Test Video",
            "url": "https://example.com/video",
            "duration": 120.5,
        }
        video = Video(entry)
        assert video.max_height == "1080"

    def test_video_max_height_custom(self):
        """Test that max_height uses custom value when set."""
        entry = {
            "id": "abc123",
            "title": "Test Video",
            "url": "https://example.com/video",
            "duration": 120.5,
            "max_height": 720,
        }
        video = Video(entry)
        assert video.max_height == 720


class TestVideoLoadFromJson:
    """Tests for Video.load_from_json method."""

    def test_load_from_json(self, tmp_path: Path):
        """Test loading a Video from a JSON file."""
        entry = {
            "id": "xyz789",
            "title": "Loaded Video",
            "url": "https://example.com/loaded",
            "duration": 300.0,
            "my_index": 5,
            "my_title": "Loaded Channel",
        }
        json_file = tmp_path / "test.link"
        json_file.write_text(json.dumps(entry))

        video = Video.load_from_json(json_file)
        assert video.id == "xyz789"
        assert video.title == "Loaded Video"
        assert video.duration == 300.0

    def test_load_from_json_deprecated_alias(self, tmp_path: Path):
        """Test that LoadFromJSON alias still works."""
        entry = {
            "id": "alias123",
            "title": "Alias Video",
            "url": "https://example.com/alias",
            "duration": 60.0,
        }
        json_file = tmp_path / "alias.link"
        json_file.write_text(json.dumps(entry))

        video = Video.LoadFromJSON(json_file)
        assert video.id == "alias123"


class TestVideoJsonFilename:
    """Tests for Video.json_filename property."""

    def test_json_filename_short_id(self):
        """Test json_filename with short ID."""
        entry = {"id": "short", "title": "T", "url": "u", "duration": 1.0}
        video = Video(entry)
        assert video.json_filename == f"short{LINK_FILE_EXTENSION}"

    def test_json_filename_long_id_truncation(self):
        """Test that json_filename truncates long IDs to 20 chars."""
        long_id = "a" * 30
        entry = {"id": long_id, "title": "T", "url": "u", "duration": 1.0}
        video = Video(entry)
        expected = "a" * 20 + LINK_FILE_EXTENSION
        assert video.json_filename == expected
        assert len(video.json_filename) == 20 + len(LINK_FILE_EXTENSION)


class TestVideoWriteJson:
    """Tests for Video.write_json method."""

    def test_write_json(self, tmp_path: Path):
        """Test writing video metadata to JSON file."""
        entry = {
            "id": "write123",
            "title": "Write Test",
            "url": "https://example.com/write",
            "duration": 180.0,
        }
        video = Video(entry)
        video.write_json(tmp_path)

        expected_file = tmp_path / video.json_filename
        assert expected_file.exists()

        with open(expected_file) as f:
            loaded = json.load(f)
        assert loaded["id"] == "write123"
        assert loaded["title"] == "Write Test"


class TestVideoDownload:
    """Tests for Video.download method."""

    @patch("videos.video.yt_dlp.YoutubeDL")
    def test_download_success(self, mock_ytdl_class: MagicMock, tmp_path: Path):
        """Test successful video download."""
        entry = {
            "id": "dl123",
            "title": "Download Test",
            "url": "https://example.com/download",
            "duration": 60.0,
            "my_title": "Test Channel",
        }
        video = Video(entry)

        # Mock the YoutubeDL instance
        mock_ytdl = MagicMock()
        mock_ytdl_class.return_value = mock_ytdl

        # Simulate progress hook being called with filename
        def download_side_effect(url: str) -> None:
            # Get the progress hook from the params
            params = mock_ytdl_class.call_args[1]["params"]
            hook = params["progress_hooks"][0]
            hook({"filename": str(tmp_path / "downloaded.mp4"), "status": "finished"})

        mock_ytdl.download.side_effect = download_side_effect

        result = video.download(tmp_path)
        assert result == tmp_path / "downloaded.mp4"
        mock_ytdl.download.assert_called_once_with(video.url)

    @patch("videos.video.yt_dlp.YoutubeDL")
    def test_download_no_filename(self, mock_ytdl_class: MagicMock, tmp_path: Path):
        """Test download when filename is not captured."""
        entry = {
            "id": "dl456",
            "title": "No Filename Test",
            "url": "https://example.com/nofile",
            "duration": 60.0,
            "my_title": "Test Channel",
        }
        video = Video(entry)

        mock_ytdl = MagicMock()
        mock_ytdl_class.return_value = mock_ytdl

        result = video.download(tmp_path)
        assert result is None
