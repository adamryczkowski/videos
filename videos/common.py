"""Common constants and utilities for the videos package.

This module contains shared constants used across the package to ensure
consistency and avoid magic values.
"""

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
