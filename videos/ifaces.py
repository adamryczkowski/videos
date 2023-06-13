from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

class IVideo(ABC):
    @staticmethod
    @abstractmethod
    def LoadFromJSON(json_path: Path):
        pass

    @property
    @abstractmethod
    def index(self) -> int:
        pass

    @property
    @abstractmethod
    def duration(self) -> float:
        pass

    @property
    @abstractmethod
    def id(self) -> float:
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        pass

    @property
    @abstractmethod
    def channel_name(self) -> str:
        pass

    @property
    @abstractmethod
    def url(self) -> str:
        pass

    @abstractmethod
    def write_json(self, cache_dir: Path):
        pass

    @property
    @abstractmethod
    def json_filename(self) -> str:
        pass

    @abstractmethod
    def download(self, dir: Path):
        pass

class IVideos(ABC):
    @property
    @abstractmethod
    def link(self) -> Path:
        pass

    @abstractmethod
    def make_folders(self):
        pass

    @property
    @abstractmethod
    def max_height(self) -> int:
        pass

    @property
    @abstractmethod
    def target_folder(self) -> Path:
        pass

    @property
    @abstractmethod
    def channel_name(self) -> str:
        pass

    @property
    @abstractmethod
    def channel_url(self) -> str:
        pass

    @property
    @abstractmethod
    def video_iterator(self) -> Iterator[IVideo]:
        pass

    @abstractmethod
    def __getitem__(self, item: int) -> IVideo:
        pass

    @abstractmethod
    def __len__(self) -> int:
        pass

    @abstractmethod
    def write_links(self):
        pass