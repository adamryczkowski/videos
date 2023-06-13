import json
from pathlib import Path
import yt_dlp


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

