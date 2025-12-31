from .videos import Videos as Videos
from .video import Video as Video
from .functions import make_links as make_links
from .functions import download_all_sequential as download_all_sequential
from .main import download as download, Main as Main
from .parallel_fetch import (
    ParallelFetcher as ParallelFetcher,
    ChannelResult as ChannelResult,
    main as main,
)

# Alias for the parallel fetch entry point
fetch_links_parallel = main

# Backward compatibility alias
download_all = download_all_sequential
