"""Main module for video download orchestration.

This module provides the Main class for managing video downloads and the
download functions for processing link queue files.
"""

import json
from pathlib import Path
from typing import Iterator

import yt_dlp

from .video import Video
from .videos import load_config, Videos


class Main:
    """Main orchestrator for video download operations.

    Manages configuration, directory structure, and provides access to
    video definitions and download queues.

    Attributes:
        _conf: Configuration dictionary loaded from TOML file.
        _prefix: Target directory prefix for downloads.
        _cache_path: Path to the cache directory.
        _base_dir: Base directory for resolving relative paths.
    """

    _conf: dict
    _prefix: Path
    _cache_path: Path
    _base_dir: Path

    def __init__(self, conf_file: Path | str = "video_downloads.toml"):
        """Initialize the Main orchestrator.

        Args:
            conf_file: Path to the main configuration TOML file.
                Defaults to "video_downloads.toml".
        """
        self._conf = load_config(conf_file)
        self._base_dir = Path(conf_file).parent
        self.make_folders()

    def make_folders(self):
        """Create required directory structure for downloads.

        Creates the link queue directory, video definition directory,
        and optionally the symlink directory if configured.
        """
        path = self.link_queue_dir
        path.mkdir(parents=True, exist_ok=True)
        path = self.video_definition_dir
        path.mkdir(parents=True, exist_ok=True)
        if self.symlink_dir is not None:
            path = self.symlink_dir
            path.mkdir(parents=True, exist_ok=True)

    @property
    def video_definition_dir(self) -> Path:
        """Get the directory containing video definition TOML files.

        Returns:
            Absolute path to the video definition directory.
        """
        path = Path(self._conf["video_definition_dir"])
        if not path.is_absolute():
            path = self._base_dir / path
        return path

    @property
    def link_queue_dir(self) -> Path:
        """Get the directory for queued download links.

        Returns:
            Absolute path to the link queue directory.
        """
        path = Path(self._conf["link_queue_dir"])
        if not path.is_absolute():
            path = self._base_dir / path
        return path

    @property
    def target_prefix(self) -> Path:
        """Get the target directory prefix for downloaded videos.

        Returns:
            Absolute path to the target directory.
        """
        path = Path(self._conf["target_dir"])
        if not path.is_absolute():
            path = self._base_dir / path
        return path

    @property
    def symlink_dir(self) -> Path | None:
        """Get the optional symlink directory.

        Returns:
            Absolute path to the symlink directory, or None if not configured.
        """
        if "symlink_dir" not in self._conf:
            return None
        path = Path(self._conf["symlink_dir"])
        if not path.is_absolute():
            path = self._base_dir / path
        return path

    @property
    def videos_iterator(self) -> Iterator[Videos]:
        """Iterate over all video channel definitions.

        Yields:
            Videos objects for each TOML file in the video definition directory.
        """
        path = self.video_definition_dir
        for file in path.glob("*.toml"):
            yield Videos(
                file, cache_dir=self.link_queue_dir, prefix_dir=self.target_prefix
            )

    def get_videos(self, filename: Path) -> Videos:
        """Load a Videos object from a specific configuration file.

        Args:
            filename: Path to the video channel configuration file.

        Returns:
            Videos object for the specified channel.
        """
        vids = Videos(filename, self.link_queue_dir, prefix_dir=self._prefix)
        return vids


def download(conf_file: str = "video_downloads.toml"):
    """Download all queued videos sequentially.

    Processes all .link files in the queue directory one by one.

    Args:
        conf_file: Path to the main configuration file.
    """
    m = Main(conf_file)
    path = m.link_queue_dir
    for json_file in path.glob("*.link"):
        download_link(json_file, m.target_prefix)
        # with open(json_file, 'rb') as f:
        #     json_entry = json.load(f)
        # vid = Video(json_entry)
        # assert str(m.link_queue_dir / vid.json_filename) == str(json_file)
        # vid.download(m.target_prefix)
        # Path(json_file).unlink()


def download_link(
    json_file: Path, target_prefix: Path, symlink_dir: Path | None = None
):
    """Download a single video from a link file.

    Reads the video metadata from the JSON link file, downloads the video,
    and removes the link file on success. On failure, renames the file
    with a .broken extension.

    Args:
        json_file: Path to the .link file containing video metadata.
        target_prefix: Directory prefix for the downloaded video.
        symlink_dir: Optional directory for creating symlinks (not implemented).
    """
    with open(str(json_file), "rb") as f:
        json_entry = json.load(f)
    vid = Video(json_entry)
    try:
        filename = vid.download(target_prefix)
        print(f"Movie saved to {filename}")
        # if symlink_dir is not None:
        #     os.symlink(str(filename), f"{str(symlink_dir)}/vid.channel_name .target_folder), target_is_directory=True)
    except yt_dlp.DownloadError:  # pyright: ignore[reportAttributeAccessIssue]
        json_file.rename(json_file.with_suffix(".broken"))
    else:
        json_file.unlink()


def test():
    """Test function to write links for all video channels."""
    m = Main()
    for vids in m.videos_iterator:
        vids.write_links()


if __name__ == "__main__":
    # test()
    download(conf_file="video_downloads.toml")
