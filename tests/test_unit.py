"""Unit tests for the videos package."""

from videos import Video, Videos, Main, download, make_links, download_all


def test_imports():
    """Test that all main exports can be imported."""
    assert Video is not None
    assert Videos is not None
    assert Main is not None
    assert download is not None
    assert make_links is not None
    assert download_all is not None


def test_video_class_exists():
    """Test that Video class can be instantiated."""
    # Video requires a dict with required fields
    video = Video(
        {
            "id": "test123",
            "title": "Test Video",
            "duration": 120.0,
            "my_index": 1,
            "my_title": "Test Channel",
        }
    )
    assert video.id == "test123"
    assert video.title == "Test Video"
    assert video.duration == 120.0
