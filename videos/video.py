import json
from pathlib import Path
import yt_dlp
from .ifaces import IVideos, IVideo


class Video(IVideo):
    _entry: dict
    _parent: IVideos

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
    def max_height(self) -> str:
        if "max_height" not in self._entry:
            return "1080"
        return self._entry["max_height"]

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

    def download(self, dir: Path)->Path|None:
        filename = ""
        def set_filename(d):
            nonlocal filename
            filename = d
        ydl_opts = {'format': f"bestvideo[height<={self.max_height}]+bestaudio/best",
                    'outtmpl': {'default': f"{dir / self.channel_name}/%(upload_date)s %(title)s.%(ext)s"},
                    'subtitleslangs': ['pl', 'en', 'ru'],
                    'writedescription': True,
                    'writesubtitles': True, 'writethumbnail': True,
                    'progress_hooks': [set_filename]}

        yt = yt_dlp.YoutubeDL(params=ydl_opts)
        yt.download(self.url)
        if filename != "":
            return Path(filename["filename"])
        else:
            return None
