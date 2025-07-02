import json
import subprocess
import sys
from pathlib import Path

from .main import Main
from .video import Video


def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


def download_all(conf_file: Path | str = "video_downloads.toml"):
    m = Main(conf_file)
    path = m.link_queue_dir
    for json_file in path.glob('*.link'):
        with open(json_file, 'rb') as f:
            json_entry = json.load(f)
        vid = Video(json_entry)
        assert str(m.link_queue_dir / vid.json_filename) == str(json_file)
        vid.download(m.target_prefix)
        Path(json_file).unlink()


def make_links(conf_file: Path | str = "video_downloads.toml"):
    install("yt-dlp")
    m = Main(conf_file)
    for vids in m.videos_iterator:
        vids.write_links()


if __name__ == '__main__':
    make_links()
