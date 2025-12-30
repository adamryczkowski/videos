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

logger = logging.getLogger(__name__)


def install(package):
    """Install a Python package using pip.

    Args:
        package: Name of the package to install.
    """
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def download_all(conf_file: Path | str = "video_downloads.toml"):
    """Download all queued videos sequentially (legacy function).

    Handles download errors by renaming failed link files to .broken
    extension instead of crashing.

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
        try:
            vid.download(m.target_prefix)
        except DownloadError as e:
            logger.error("Download failed for %s: %s", vid.title, e)
            json_file.rename(json_file.with_suffix(".broken"))
        else:
            Path(json_file).unlink()


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
