"""Unit tests for the videos package."""

from videos import Video, Videos, Main, download, make_links, download_all


def test_imports():
    """Test that all public API imports work."""
    assert Video is not None
    assert Videos is not None
    assert Main is not None
    assert download is not None
    assert make_links is not None
    assert download_all is not None


def test_video_class_exists():
    """Test that Video class has expected methods."""
    assert hasattr(Video, "LoadFromJSON")
    assert hasattr(Video, "download")
    assert hasattr(Video, "write_json")
