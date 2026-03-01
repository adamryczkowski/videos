"""Common constants and utilities for the videos package.

This module contains shared constants used across the package to ensure
consistency and avoid magic values.
"""

from typing import Any

# File extension for video link queue files
LINK_FILE_EXTENSION = ".link"

# Default maximum video height for quality selection
DEFAULT_MAX_HEIGHT = 1080

# Default number of worker threads for concurrent downloads
DEFAULT_WORKER_COUNT = 3

# Default subtitle languages to download
DEFAULT_SUBTITLE_LANGUAGES = ["pl", "en", "ru"]

# Default browser for cookie-based authentication
DEFAULT_BROWSER = "firefox"

# Default YouTube player clients for extractor_args
# As of 2026, android_sdkless is deprecated and must be excluded
# See: https://github.com/yt-dlp/yt-dlp/issues/15012
DEFAULT_PLAYER_CLIENTS = ["default", "-android_sdkless"]

# Default FFmpeg downloader arguments for network resilience
# These help recover from network interruptions during downloads
DEFAULT_FFMPEG_ARGS = [
    "-reconnect",
    "1",
    "-reconnect_streamed",
    "1",
    "-reconnect_delay_max",
    "5",
]

# Default sleep intervals to avoid rate limiting (in seconds)
DEFAULT_MIN_SLEEP_INTERVAL = 1
DEFAULT_MAX_SLEEP_INTERVAL = 5


def build_cookie_opts(
    cookies_file: str | None = None, browser: str = DEFAULT_BROWSER
) -> dict[str, Any]:
    """Build yt-dlp cookie authentication options.

    Args:
        cookies_file: Path to a Netscape-format cookies file.
            Takes priority over browser extraction when set.
        browser: Browser name for cookie extraction fallback.

    Returns:
        Dict with either 'cookiefile' or 'cookiesfrombrowser' key.
    """
    if cookies_file:
        return {"cookiefile": cookies_file}
    return {"cookiesfrombrowser": (browser,)}
