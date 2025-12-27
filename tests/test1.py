import pytest

from videos import download, Main


@pytest.mark.integration
def test_single_download():
    download(conf_file="../video_downloads.toml")


@pytest.mark.integration
def test_discovery():
    m = Main(conf_file="../video_downloads.toml")
    for vids in m.videos_iterator:
        vids.write_links()


if __name__ == "__main__":
    test_discovery()
    test_single_download()
