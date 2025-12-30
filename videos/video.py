"""Video module for individual video handling.

This module provides the Video class for representing and downloading
individual videos using yt-dlp.
"""

import json
from pathlib import Path

import yt_dlp

from .ifaces import IVideos, IVideo


class Video(IVideo):
    """Represents a single video to be downloaded.

    Encapsulates video metadata and provides methods for downloading
    and serializing video information.

    Attributes:
        _entry: Dictionary containing video metadata from yt-dlp.
        _parent: Reference to parent Videos collection (unused).
    """

    _entry: dict
    _parent: IVideos

    @staticmethod
    def LoadFromJSON(json_path: Path):  # pyright: ignore[reportIncompatibleMethodOverride]
        """Load a Video instance from a JSON link file.

        Args:
            json_path: Path to the .link JSON file.

        Returns:
            Video instance populated with metadata from the file.
        """
        with open(str(json_path), "rb") as f:
            json_entry = json.load(f)
        vid = Video(json_entry)
        return vid

    def __init__(self, entry: dict):
        """Initialize a Video from metadata dictionary.

        Args:
            entry: Dictionary containing video metadata including
                id, title, url, duration, and custom fields.
        """
        self._entry = entry

    @property
    def index(self) -> int:
        """Get the video's index in the playlist."""
        return self._entry["my_index"]

    # @property
    # def entry_json_file(self) -> Path:
    #     return self._path

    @property
    def duration(self) -> float:
        """Get the video duration in seconds."""
        return self._entry["duration"]

    @property
    def id(self) -> str:
        """Get the unique video identifier."""
        return self._entry["id"]

    @property
    def title(self) -> str:
        """Get the video title."""
        return self._entry["title"]

    @property
    def channel_name(self) -> str:
        """Get the channel/folder name for organizing downloads."""
        return self._entry["my_title"]

    @property
    def max_height(self) -> str:
        """Get the maximum video height for quality selection.

        Returns:
            Maximum height as string, defaults to "1080".
        """
        if "max_height" not in self._entry:
            return "1080"
        return self._entry["max_height"]

    @property
    def url(self) -> str:
        """Get the video URL."""
        return self._entry["url"]

    def write_json(self, cache_dir: Path):
        """Write video metadata to a JSON link file.

        Args:
            cache_dir: Directory to write the .link file to.
        """
        file = cache_dir / self.json_filename
        json_dump = json.dumps(self._entry)
        with open(str(file), "w") as outfile:
            outfile.write(json_dump)

    @property
    def json_filename(self) -> str:
        """Get the filename for the JSON link file.

        Returns:
            Filename based on first 20 chars of video ID with .link extension.
        """
        strhash = str(self.id)
        file = strhash[:20] + ".link"
        return file

    def download(self, dir: Path) -> Path | None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Download the video using yt-dlp.

        Downloads the video with configured quality settings, subtitles,
        and metadata (description, thumbnail).

        Args:
            dir: Target directory for the downloaded video.

        Returns:
            Path to the downloaded file, or None if filename not captured.

        Raises:
            yt_dlp.DownloadError: If the download fails.
        """
        filename = ""

        def set_filename(d):
            nonlocal filename
            filename = d

        ydl_opts = {
            "format": f"bestvideo[height<={self.max_height}][vcodec!~='vp0?9']+bestaudio/best",
            "outtmpl": {
                "default": f"{dir / self.channel_name}/%(upload_date)s %(title)s.%(ext)s"
            },
            "subtitleslangs": ["pl", "en", "ru"],
            "writedescription": True,
            "writesubtitles": True,
            "writethumbnail": True,
            "progress_hooks": [set_filename],
            "cookiesfrombrowser": ("firefox",),
            "extractor_args": {
                "youtube": {
                    "player_client": ["default", "web_safari"],
                    "player_js_version": ["actual"],
                }
            },
        }

        yt = yt_dlp.YoutubeDL(params=ydl_opts)  # pyright: ignore[reportArgumentType]
        yt.download(self.url)
        if filename != "":
            return Path(filename["filename"])
        else:
            return None
