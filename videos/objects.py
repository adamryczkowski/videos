import json
from pathlib import Path
from typing import Iterator

import toml
import yt_dlp

from videos.common import load_config


class Video:
    _entry: dict

    @staticmethod
    def LoadFromJSON(json_path: Path):
        with open(str(json_path), 'rb') as f:
            json_entry = json.load(f)
        vid = Video(json_entry)
        return vid

    def __init__(self, entry: dict):
        self._entry = entry

    @property
    def index(self) -> int:
        return self._entry["my_index"]

    # @property
    # def entry_json_file(self) -> Path:
    #     return self._path

    @property
    def duration(self) -> float:
        return self._entry["duration"]

    @property
    def id(self) -> float:
        return self._entry["id"]

    @property
    def title(self) -> str:
        return self._entry["title"]

    @property
    def channel_name(self) -> str:
        return self._entry["my_title"]

    @property
    def url(self) -> str:
        return self._entry["url"]

    def write_json(self, cache_dir: Path):
        file = cache_dir / self.json_filename
        json_dump = json.dumps(self._entry)
        with open(str(file), "w") as outfile:
            outfile.write(json_dump)

    @property
    def json_filename(self) -> str:
        strhash = self.id
        file = strhash[:20] + ".link"
        return file

    def download(self, dir: Path):
        ydl_opts = {'format': "bestvideo[height<=1080]+bestaudio/best",
                    'outtmpl': {'default': f"{dir / self.channel_name}/%(upload_date)s %(title)s.%(ext)s"},
                    'subtitleslangs': ['pl', 'en', 'ru'],
                    'writesubtitles': True, 'writethumbnail': True}
        yt = yt_dlp.YoutubeDL(params=ydl_opts)
        yt.download(self.url)



class Videos:
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
    def target_folder(self) -> Path:
        path = Path(self._conf["target_folder"])
        return self._prefix_dir / path

    def _get_new_links(self):
        if self._info is not None:
            return
        print(f"Checking for new videos from {self._conf['target_folder']}...", end="")

        if "last_video" in self._conf:
            target_id = self._conf["last_video"]
            yt = yt_dlp.YoutubeDL(params={
                "extract_flat": 'in_playlist', "simulate": True, "dump_single_json": True,
                "playlist_items": f"0:5:1",
                "quiet": True})
            ans = yt.extract_info(url=self.link)
            for i, entry in enumerate(ans["entries"]):
                if entry["id"] == target_id:
                    ans["entries"] = ans["entries"][0:i]
                    self._info = ans
                    if len(ans["entries"]) == 0:
                        print(" nothing.")
                    elif len(ans["entries"]) == 1:
                        print(" 1 video found.")
                    else:
                        print(f" {len(ans['entries'])} videos found.")
                    return

        yt = yt_dlp.YoutubeDL(params={
            "extract_flat": 'in_playlist', "simulate": True, "dump_single_json": True, "quiet": True})
        ans = yt.extract_info(url=self.link)
        if ans["webpage_url_domain"] == 'piped.video':
            ans = ans["entries"][0]
        entries = ans["entries"]
        le = len(entries)
        entries = entries[0:le - self._conf["last_download_index"]]
        ans["entries"] = list(reversed(entries))
        if len(ans["entries"]) == 0:
            print(" nothing.")
        elif len(ans["entries"]) == 1:
            print(" 1 video found.")
        else:
            print(f" {len(ans['entries'])} videos found.")

        self._info = ans

    @property
    def channel_name(self) -> str:
        self._get_new_links()
        return self._info["channel"]

    @property
    def channel_url(self) -> str:
        self._get_new_links()
        return self._info["channel_url"]

    @property
    def video_iterator(self) -> Iterator[Video]:
        self._get_new_links()
        for i, entry in enumerate(self._info["entries"]):
            entry["my_index"] = i
            entry["my_title"] = self._conf["target_folder"]
            vid = Video(entry)
            yield vid

    def __getitem__(self, item: int) -> Video:
        self._get_new_links()
        self._info["entries"][item]["my_index"] = item
        self._info["entries"][item]["my_title"] = self._conf["target_folder"]
        vid = Video(self._info["entries"][item])
        return vid

    def __len__(self) -> int:
        self._get_new_links()
        return len(self._info["entries"])

    def write_links(self):
        self._get_new_links()
        self.make_folders()
        last_index = self._conf["last_download_index"]
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
    def videos_iterator(self) -> Iterator[Videos]:
        path = self.video_definition_dir
        for file in path.glob('*.toml'):
            yield Videos(file, cache_dir=self.link_queue_dir, prefix_dir=self.target_prefix)

    def get_videos(self, filename: Path) -> Videos:
        vids = Videos(filename, self.link_queue_dir, prefix_dir=self._prefix)
        return vids


def download(conf_file:str="video_downloads.toml"):
    m = Main(conf_file)
    path = m.link_queue_dir
    for json_file in path.glob('*.link'):
        download_link(json_file, m.target_prefix)
        # with open(json_file, 'rb') as f:
        #     json_entry = json.load(f)
        # vid = Video(json_entry)
        # assert str(m.link_queue_dir / vid.json_filename) == str(json_file)
        # vid.download(m.target_prefix)
        # Path(json_file).unlink()


def download_link(json_file: Path, target_prefix: Path):
    with open(str(json_file), 'rb') as f:
        json_entry = json.load(f)
    vid = Video(json_entry)
    try:
        vid.download(target_prefix)
    except yt_dlp.DownloadError as d:
        json_file.rename(json_file.with_suffix(".broken"))
    else:
        json_file.unlink()


def test():
    m = Main()
    for vids in m.videos_iterator:
        vids.write_links()


if __name__ == '__main__':
    # test()
    download(conf_file="video_downloads.toml")
