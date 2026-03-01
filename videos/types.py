"""Type definitions for the videos package.

This module provides TypedDict definitions for yt-dlp responses
and other structured data used throughout the package.
"""

from typing import NotRequired, TypedDict


class VideoEntry(TypedDict):
    """Represents a video entry from yt-dlp playlist extraction.

    This TypedDict defines the structure of video metadata returned
    by yt-dlp when extracting playlist information.

    Attributes:
        id: Unique video identifier.
        title: Video title.
        url: Video URL.
        duration: Video duration in seconds.
        my_index: Custom field for playlist position (added by Videos).
        my_title: Custom field for channel/folder name (added by Videos).
        max_height: Maximum video height for quality selection (added by Videos).
    """

    id: str
    title: str
    url: str
    duration: float
    my_index: NotRequired[int]
    my_title: NotRequired[str]
    max_height: NotRequired[int]
    cookies_file: NotRequired[str]


class PlaylistInfo(TypedDict):
    """Represents playlist information from yt-dlp extraction.

    This TypedDict defines the structure of playlist metadata returned
    by yt-dlp when extracting playlist information.

    Attributes:
        entries: List of video entries in the playlist.
        channel: Channel name.
        channel_url: Channel URL.
        webpage_url_domain: Domain of the webpage (e.g., youtube.com, piped.video).
    """

    entries: list[VideoEntry]
    channel: str
    channel_url: str
    webpage_url_domain: NotRequired[str]


class ProgressHookInfo(TypedDict):
    """Represents progress hook callback information from yt-dlp.

    This TypedDict defines the structure of the dictionary passed
    to progress hooks during download.

    Attributes:
        filename: Path to the file being downloaded.
        status: Download status (downloading, finished, error).
        downloaded_bytes: Number of bytes downloaded so far.
        total_bytes: Total file size in bytes (may be None).
        elapsed: Time elapsed since download started.
        speed: Download speed in bytes per second.
    """

    filename: NotRequired[str]
    status: NotRequired[str]
    downloaded_bytes: NotRequired[int]
    total_bytes: NotRequired[int]
    elapsed: NotRequired[float]
    speed: NotRequired[float]
