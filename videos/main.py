import json
from pathlib import Path
from typing import Iterator

import yt_dlp

from .video import Video
from .videos import load_config, Videos


class Main:
    _conf: dict
    _prefix: Path
    _cache_path: Path
    _base_dir: Path

    def __init__(self, conf_file: Path | str = "video_downloads.toml"):
        self._conf = load_config(conf_file)
        self._base_dir = Path(conf_file).parent
        self.make_folders()

    def make_folders(self):
        path = self.link_queue_dir
        path.mkdir(parents=True, exist_ok=True)
        path = self.video_definition_dir
        path.mkdir(parents=True, exist_ok=True)
        if self.symlink_dir is not None:
            path = self.symlink_dir
            path.mkdir(parents=True, exist_ok=True)

    @property
    def video_definition_dir(self) -> Path:
        path = Path(self._conf["video_definition_dir"])
        if not path.is_absolute():
            path = self._base_dir / path
        return path

    @property
    def link_queue_dir(self) -> Path:
        path = Path(self._conf["link_queue_dir"])
        if not path.is_absolute():
            path = self._base_dir / path
        return path

    @property
    def target_prefix(self) -> Path:
        path = Path(self._conf["target_dir"])
        if not path.is_absolute():
            path = self._base_dir / path
        return path

    @property
    def symlink_dir(self) -> Path | None:
        if "symlink_dir" not in self._conf:
            return None
        path = Path(self._conf["symlink_dir"])
        if not path.is_absolute():
            path = self._base_dir / path
        return path

    @property
    def videos_iterator(self) -> Iterator[Videos]:
        path = self.video_definition_dir
        for file in path.glob("*.toml"):
            yield Videos(
                file, cache_dir=self.link_queue_dir, prefix_dir=self.target_prefix
            )

    def get_videos(self, filename: Path) -> Videos:
        vids = Videos(filename, self.link_queue_dir, prefix_dir=self._prefix)
        return vids


def download(conf_file: str = "video_downloads.toml"):
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
    m = Main()
    for vids in m.videos_iterator:
        vids.write_links()


if __name__ == "__main__":
    # test()
    download(conf_file="video_downloads.toml")
