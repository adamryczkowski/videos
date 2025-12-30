from .videos import Videos as Videos
from .video import Video as Video
from .functions import make_links as make_links
from .functions import download_all_sequential as download_all_sequential
from .main import download as download, Main as Main

# Backward compatibility alias
download_all = download_all_sequential
