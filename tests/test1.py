from videos import *

def test_single_download():
    download(conf_file="../video_downloads.toml")

def test_discovery():
    m = Main(conf_file="../video_downloads.toml")
    for vids in m.videos_iterator:
        vids.write_links()


if __name__ == '__main__':
    test_discovery()
    test_single_download()