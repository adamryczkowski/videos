"""Videos module for managing video channel collections.

This module provides the Videos class for fetching and managing
video playlists from YouTube and other sources using yt-dlp.
"""

import logging
import tomllib
from pathlib import Path
from typing import Any, Iterator

import toml
import yt_dlp

from .common import DEFAULT_MAX_HEIGHT
from .ifaces import IVideo, IVideos
from .video import Video

logger = logging.getLogger(__name__)


def load_config(conf_file: Path | str) -> dict[str, Any]:
    """Load and validate a TOML configuration file.

    Args:
        conf_file: Path to the TOML configuration file.

    Returns:
        Configuration dictionary with defaults applied for
        max_height (1080) and last_download_index (0).

    Raises:
        ValueError: If required configuration keys are missing.
    """
    with open(str(conf_file), "rb") as f:
        data = tomllib.load(f)

    # Validate required keys for channel config
    if "link" in data or "target_folder" in data:
        required_keys = ["link", "target_folder"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required configuration key: {key}")

    # Apply defaults
    data.setdefault("max_height", DEFAULT_MAX_HEIGHT)
    data.setdefault("last_download_index", 0)
    return data


class Videos(IVideos):
    """Represents a collection of videos from a channel or playlist.

    Manages fetching video metadata from YouTube/other sources,
    tracking download progress, and generating download queue files.

    Attributes:
        _conf: Channel configuration dictionary.
        _cache_dir: Directory for storing link queue files.
        _info: Cached playlist information from yt-dlp.
        _prefix_dir: Target directory prefix for downloads.
        _conf_file: Path to the channel configuration file.
    """

    _conf: dict[str, Any]
    _cache_dir: Path
    _info: dict[str, Any] | None
    _prefix_dir: Path
    _conf_file: Path

    def __init__(self, conf_file: Path, cache_dir: Path, prefix_dir: Path):
        """Initialize a Videos collection.

        Args:
            conf_file: Path to the channel configuration TOML file.
            cache_dir: Directory for storing .link queue files.
            prefix_dir: Target directory prefix for downloads.
        """
        self._conf = load_config(conf_file)
        self._conf_file = conf_file
        self._cache_dir = cache_dir
        self._info = None
        self._prefix_dir = prefix_dir
        self.make_folders()

    @property
    def link(self) -> Path:
        """Get the channel/playlist URL."""
        return self._conf["link"]

    def make_folders(self):
        """Create the target folder for downloaded videos."""
        self.target_folder.mkdir(parents=True, exist_ok=True)

    @property
    def max_height(self) -> int:
        """Get the maximum video height for quality selection."""
        return self._conf["max_height"]

    @property
    def target_folder(self) -> Path:
        """Get the full path to the target download folder."""
        path = Path(self._conf["target_folder"])
        return self._prefix_dir / path

    def _get_new_links(self):
        """Fetch new video links from the channel/playlist.

        Uses yt-dlp to extract playlist information. If last_video is set,
        only fetches videos newer than that. Otherwise fetches all videos
        up to last_download_index.

        Results are cached in self._info.
        """
        if self._info is not None:
            return
        logger.info("Checking for new videos from %s...", self._conf["target_folder"])

        if "last_video" in self._conf:
            target_id = self._conf["last_video"]
            yt = yt_dlp.YoutubeDL(
                params={  # pyright: ignore[reportArgumentType]
                    "extract_flat": "in_playlist",
                    "simulate": True,
                    "dump_single_json": True,
                    "playlist_items": "0:5:1",
                    "quiet": True,
                    "cookiesfrombrowser": ("firefox",),
                    "extractor_args": {
                        "youtube": {
                            "player_client": ["default", "web_safari"],
                            "player_js_version": ["actual"],
                        }
                    },
                }
            )
            ans = yt.extract_info(url=str(self.link))
            for i, entry in enumerate(ans["entries"]):  # pyright: ignore[reportGeneralTypeIssues]
                if entry["id"] == target_id:
                    ans["entries"] = ans["entries"][0:i]  # pyright: ignore[reportGeneralTypeIssues]
                    self._info = ans  # pyright: ignore[reportAttributeAccessIssue]
                    num_entries = len(ans["entries"])  # pyright: ignore[reportGeneralTypeIssues]
                    if num_entries == 0:
                        logger.info("No new videos found.")
                    elif num_entries == 1:
                        logger.info("1 video found.")
                    else:
                        logger.info("%d videos found.", num_entries)
                    return

        yt = yt_dlp.YoutubeDL(
            params={  # pyright: ignore[reportArgumentType]
                "extract_flat": "in_playlist",
                "simulate": True,
                "dump_single_json": True,
                "quiet": True,
                "cookiesfrombrowser": ("firefox",),
                "extractor_args": {
                    "youtube": {
                        "player_client": ["default", "web_safari"],
                        "player_js_version": ["actual"],
                    }
                },
            }
        )
        ans = yt.extract_info(url=str(self.link))
        if ans["webpage_url_domain"] == "piped.video":  # pyright: ignore[reportGeneralTypeIssues]
            ans = ans["entries"][0]  # pyright: ignore[reportGeneralTypeIssues]
        entries = ans["entries"]  # pyright: ignore[reportGeneralTypeIssues]
        num_total = len(entries)
        entries = entries[0 : num_total - self._conf["last_download_index"]]
        ans["entries"] = list(reversed(entries))  # pyright: ignore[reportGeneralTypeIssues]
        num_entries = len(ans["entries"])  # pyright: ignore[reportGeneralTypeIssues]
        if num_entries == 0:
            logger.info("No new videos found.")
        elif num_entries == 1:
            logger.info("1 video found.")
        else:
            logger.info("%d videos found.", num_entries)

        self._info = ans  # pyright: ignore[reportAttributeAccessIssue]

    @property
    def channel_name(self) -> str:
        """Get the channel name from playlist metadata."""
        self._get_new_links()
        return self._info["channel"]  # pyright: ignore[reportOptionalSubscript]

    @property
    def channel_url(self) -> str:
        """Get the channel URL from playlist metadata."""
        self._get_new_links()
        return self._info["channel_url"]  # pyright: ignore[reportOptionalSubscript]

    @property
    def video_iterator(self) -> Iterator[IVideo]:
        """Iterate over new videos in the playlist.

        Yields:
            Video objects for each new video, with metadata populated.
        """
        self._get_new_links()
        for i, entry in enumerate(self._info["entries"]):  # pyright: ignore[reportOptionalSubscript]
            entry["my_index"] = i
            entry["my_title"] = self._conf["target_folder"]
            entry["max_height"] = self.max_height
            vid = Video(entry)
            yield vid

    def __getitem__(self, item: int) -> IVideo:
        """Get a video by index.

        Args:
            item: Index of the video in the playlist.

        Returns:
            Video object with metadata populated.
        """
        self._get_new_links()
        self._info["entries"][item]["my_index"] = item  # pyright: ignore[reportOptionalSubscript]
        self._info["entries"][item]["my_title"] = self._conf["target_folder"]  # pyright: ignore[reportOptionalSubscript]
        self._info["entries"][item]["max_height"] = self.max_height  # pyright: ignore[reportOptionalSubscript]
        vid = Video(self._info["entries"][item])  # pyright: ignore[reportOptionalSubscript]
        return vid

    def __len__(self) -> int:
        """Get the number of new videos."""
        self._get_new_links()
        return len(self._info["entries"])  # pyright: ignore[reportOptionalSubscript]

    def write_links(self):
        """Write link files for all new videos.

        Creates .link files in the cache directory for each new video,
        updates the configuration with download progress, and saves
        the updated configuration.
        """
        self._get_new_links()
        self.make_folders()
        for i in range(len(self)):
            entry = self[i]
            entry.write_json(self._cache_dir)
            self._conf["last_download_index"] = self._conf["last_download_index"] + 1
            self._conf["last_video"] = entry.id
            logger.info("New video from %s: %s", entry.channel_name, entry.title)
            with open(self._conf_file, "w") as toml_file:
                toml.dump(self._conf, toml_file)
