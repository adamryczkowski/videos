"""Utility functions for video download operations.

This module provides helper functions for downloading videos and
generating link queue files.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path

from yt_dlp.utils import DownloadError

from .main import Main
from .video import Video

# Configure logging for CLI entry points
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def install(package):
    """Install a Python package using pip.

    Args:
        package: Name of the package to install.
    """
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def download_all_sequential(conf_file: Path | str = "video_downloads.toml"):
    """Download all queued videos sequentially (legacy function).

    This is the single-threaded version of video downloading.
    For concurrent downloads, use videos.threads.main() instead.

    Handles download errors by renaming failed link files to .broken
    extension instead of crashing. Provides detailed error diagnostics
    for common issues like 403 Forbidden (SABR blocking) and sign-in
    requirements.

    Args:
        conf_file: Path to the main configuration file.
    """
    m = Main(conf_file)
    path = m.link_queue_dir
    for json_file in path.glob("*.link"):
        with open(json_file, "rb") as f:
            json_entry = json.load(f)
        vid = Video(json_entry)
        assert str(m.link_queue_dir / vid.json_filename) == str(json_file)
        logger.info("Starting download: %s", vid.title)
        try:
            filename = vid.download(m.target_prefix)
            logger.info("Movie saved to %s", filename)
        except DownloadError as e:
            error_msg = str(e)
            # Check for specific error types to provide better diagnostics
            if "403" in error_msg or "Forbidden" in error_msg:
                logger.error(
                    "Download failed for '%s' with 403 Forbidden. "
                    "This is likely due to YouTube's SABR blocking. "
                    "Ensure Deno is installed and in PATH, and try updating yt-dlp. "
                    "Error: %s",
                    vid.title,
                    error_msg,
                )
            elif "Sign in" in error_msg or "bot" in error_msg.lower():
                logger.error(
                    "Download failed for '%s': YouTube requires sign-in. "
                    "Ensure cookies are properly configured from Firefox. "
                    "Error: %s",
                    vid.title,
                    error_msg,
                )
            else:
                logger.error("Download failed for '%s': %s", vid.title, error_msg)
            json_file.rename(json_file.with_suffix(".broken"))
        except Exception as e:
            logger.exception("Unexpected error downloading '%s': %s", vid.title, e)
            json_file.rename(json_file.with_suffix(".broken"))
        else:
            Path(json_file).unlink()
            logger.info("Successfully completed download: %s", vid.title)


def make_links(conf_file: Path | str = "video_downloads.toml"):
    """Fetch and queue new videos from all configured channels.

    Installs yt-dlp if needed, then iterates through all channel
    configurations and writes .link files for new videos.

    Args:
        conf_file: Path to the main configuration file.
    """
    install("yt-dlp")
    m = Main(conf_file)
    for vids in m.videos_iterator:
        vids.write_links()


if __name__ == "__main__":
    make_links()
