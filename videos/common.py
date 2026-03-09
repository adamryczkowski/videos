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
# Snap Chromium stores cookies outside the standard path;
# the profile must point to the snap data directory.
DEFAULT_BROWSER = "chromium"
DEFAULT_BROWSER_PROFILE = "/home/adam/snap/chromium/common/chromium/Default"

# Default YouTube player clients for extractor_args
# As of 2026, android_sdkless is deprecated and must be excluded
# See: https://github.com/yt-dlp/yt-dlp/issues/15012
DEFAULT_PLAYER_CLIENTS = ["default", "tv", "-android_sdkless"]

# Player clients optimized for age-restricted content retry
# tv_downgraded + web_creator can often bypass age-gate without full OAuth
AGE_RESTRICTED_PLAYER_CLIENTS = [
    "tv",
    "web_embedded",
    "web_creator",
    "-android_sdkless",
]

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

# JavaScript runtime for yt-dlp's challenge solver and POT provider.
# deno is the yt-dlp default but may not be installed; node is widely available.
DEFAULT_JS_RUNTIMES = {"node": {}, "deno": {}}

# Remote component sources for auto-updating the EJS challenge solver.
DEFAULT_REMOTE_COMPONENTS = ["ejs:github"]


def build_cookie_opts(
    cookies_file: str | None = None,
    browser: str = DEFAULT_BROWSER,
    browser_profile: str | None = DEFAULT_BROWSER_PROFILE,
) -> dict[str, Any]:
    """Build yt-dlp cookie authentication options.

    Args:
        cookies_file: Path to a Netscape-format cookies file.
            Takes priority over browser extraction when set.
        browser: Browser name for cookie extraction fallback.
        browser_profile: Browser profile path (needed for snap/flatpak installs).

    Returns:
        Dict with either 'cookiefile' or 'cookiesfrombrowser' key.
    """
    if cookies_file:
        return {"cookiefile": cookies_file}
    return {"cookiesfrombrowser": (browser, browser_profile, None, None)}
