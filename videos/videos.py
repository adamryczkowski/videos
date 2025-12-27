import tomllib
from pathlib import Path
from typing import Iterator

import toml
import yt_dlp

from .ifaces import IVideo, IVideos
from .video import Video


def load_config(conf_file: Path | str) -> dict:
    with open(str(conf_file), "rb") as f:
        data = tomllib.load(f)
    if "max_height" not in data:
        data["max_height"] = 1080
    if "last_download_index" not in data:
        data["last_download_index"] = 0
    return data


class Videos(IVideos):
    _conf: dict
    _cache_dir: Path
    _info: dict | None
    _prefix_dir: Path
    _conf_file: Path

    def __init__(self, conf_file: Path, cache_dir: Path, prefix_dir: Path):
        self._conf = load_config(conf_file)
        self._conf_file = conf_file
        self._cache_dir = cache_dir
        self._info = None
        self._prefix_dir = prefix_dir
        self.make_folders()

    @property
    def link(self) -> Path:
        return self._conf["link"]

    def make_folders(self):
        self.target_folder.mkdir(parents=True, exist_ok=True)

    @property
    def max_height(self) -> int:
        return self._conf["max_height"]

    @property
    def target_folder(self) -> Path:
        path = Path(self._conf["target_folder"])
        return self._prefix_dir / path

    def _get_new_links(self):
        if self._info is not None:
            return
        print(f"Checking for new videos from {self._conf['target_folder']}...", end="")

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
                    if len(ans["entries"]) == 0:  # pyright: ignore[reportGeneralTypeIssues]
                        print(" nothing.")
                    elif len(ans["entries"]) == 1:  # pyright: ignore[reportGeneralTypeIssues]
                        print(" 1 video found.")
                    else:
                        print(f" {len(ans['entries'])} videos found.")  # pyright: ignore[reportGeneralTypeIssues]
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
        le = len(entries)
        entries = entries[0 : le - self._conf["last_download_index"]]
        ans["entries"] = list(reversed(entries))  # pyright: ignore[reportGeneralTypeIssues]
        if len(ans["entries"]) == 0:  # pyright: ignore[reportGeneralTypeIssues]
            print(" nothing.")
        elif len(ans["entries"]) == 1:  # pyright: ignore[reportGeneralTypeIssues]
            print(" 1 video found.")
        else:
            print(f" {len(ans['entries'])} videos found.")  # pyright: ignore[reportGeneralTypeIssues]

        self._info = ans  # pyright: ignore[reportAttributeAccessIssue]

    @property
    def channel_name(self) -> str:
        self._get_new_links()
        return self._info["channel"]  # pyright: ignore[reportOptionalSubscript]

    @property
    def channel_url(self) -> str:
        self._get_new_links()
        return self._info["channel_url"]  # pyright: ignore[reportOptionalSubscript]

    @property
    def video_iterator(self) -> Iterator[IVideo]:
        self._get_new_links()
        for i, entry in enumerate(self._info["entries"]):  # pyright: ignore[reportOptionalSubscript]
            entry["my_index"] = i
            entry["my_title"] = self._conf["target_folder"]
            entry["max_height"] = self.max_height
            vid = Video(entry)
            yield vid

    def __getitem__(self, item: int) -> IVideo:
        self._get_new_links()
        self._info["entries"][item]["my_index"] = item  # pyright: ignore[reportOptionalSubscript]
        self._info["entries"][item]["my_title"] = self._conf["target_folder"]  # pyright: ignore[reportOptionalSubscript]
        self._info["entries"][item]["max_height"] = self.max_height  # pyright: ignore[reportOptionalSubscript]
        vid = Video(self._info["entries"][item])  # pyright: ignore[reportOptionalSubscript]
        return vid

    def __len__(self) -> int:
        self._get_new_links()
        return len(self._info["entries"])  # pyright: ignore[reportOptionalSubscript]

    def write_links(self):
        self._get_new_links()
        self.make_folders()
        _ = self._conf["last_download_index"]  # noqa: F841
        for i in range(0, len(self)):
            entry = self[i]
            entry.write_json(self._cache_dir)
            self._conf["last_download_index"] = self._conf["last_download_index"] + 1
            self._conf["last_video"] = entry.id
            print(f"New video from {entry.channel_name}: {entry.title}")
            with open(self._conf_file, "w") as toml_file:
                toml.dump(self._conf, toml_file)

        # self._info["last_download_index"] = len(self)
        # with open(self._conf_file, "w") as toml_file:
        #     toml.dump(self._info, toml_file)
