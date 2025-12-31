"""Unit tests for the parallel fetch functionality.

These tests follow TDD approach - written before the implementation.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestChannelResult:
    """Tests for the ChannelResult dataclass."""

    def test_channel_result_creation_success(self):
        """Test creating a successful ChannelResult."""
        from videos.parallel_fetch import ChannelResult

        result = ChannelResult(
            channel_name="TestChannel",
            config_file=Path("/path/to/config.toml"),
            new_videos=5,
            success=True,
            error=None,
        )
        assert result.channel_name == "TestChannel"
        assert result.new_videos == 5
        assert result.success is True
        assert result.error is None

    def test_channel_result_creation_failure(self):
        """Test creating a failed ChannelResult."""
        from videos.parallel_fetch import ChannelResult

        result = ChannelResult(
            channel_name="FailedChannel",
            config_file=Path("/path/to/config.toml"),
            new_videos=0,
            success=False,
            error="Network timeout",
        )
        assert result.channel_name == "FailedChannel"
        assert result.new_videos == 0
        assert result.success is False
        assert result.error == "Network timeout"


class TestParallelFetcher:
    """Tests for the ParallelFetcher class."""

    def test_parallel_fetcher_default_worker_count(self):
        """Test that ParallelFetcher defaults to 5 workers."""
        from videos.parallel_fetch import ParallelFetcher

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create minimal config file
            config_path = Path(tmpdir) / "video_downloads.toml"
            config_path.write_text(
                """
video_definition_dir = "channels"
link_queue_dir = "queue"
target_dir = "downloads"
"""
            )
            # Create required directories
            (Path(tmpdir) / "channels").mkdir()
            (Path(tmpdir) / "queue").mkdir()
            (Path(tmpdir) / "downloads").mkdir()

            fetcher = ParallelFetcher(conf_file=config_path)
            assert fetcher.worker_count == 5

    def test_parallel_fetcher_custom_worker_count(self):
        """Test that ParallelFetcher accepts custom worker count."""
        from videos.parallel_fetch import ParallelFetcher

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "video_downloads.toml"
            config_path.write_text(
                """
video_definition_dir = "channels"
link_queue_dir = "queue"
target_dir = "downloads"
"""
            )
            (Path(tmpdir) / "channels").mkdir()
            (Path(tmpdir) / "queue").mkdir()
            (Path(tmpdir) / "downloads").mkdir()

            fetcher = ParallelFetcher(conf_file=config_path, worker_count=10)
            assert fetcher.worker_count == 10

    def test_parallel_fetcher_quiet_mode(self):
        """Test that ParallelFetcher accepts quiet mode flag."""
        from videos.parallel_fetch import ParallelFetcher

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "video_downloads.toml"
            config_path.write_text(
                """
video_definition_dir = "channels"
link_queue_dir = "queue"
target_dir = "downloads"
"""
            )
            (Path(tmpdir) / "channels").mkdir()
            (Path(tmpdir) / "queue").mkdir()
            (Path(tmpdir) / "downloads").mkdir()

            fetcher = ParallelFetcher(conf_file=config_path, quiet=True)
            assert fetcher.quiet is True

    def test_parallel_fetcher_collects_channel_configs(self):
        """Test that ParallelFetcher collects all channel config files."""
        from videos.parallel_fetch import ParallelFetcher

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "video_downloads.toml"
            config_path.write_text(
                """
video_definition_dir = "channels"
link_queue_dir = "queue"
target_dir = "downloads"
"""
            )
            channels_dir = Path(tmpdir) / "channels"
            channels_dir.mkdir()
            (Path(tmpdir) / "queue").mkdir()
            (Path(tmpdir) / "downloads").mkdir()

            # Create some channel config files
            (channels_dir / "channel1.toml").write_text(
                'link = "https://youtube.com/c/channel1"\ntarget_folder = "ch1"'
            )
            (channels_dir / "channel2.toml").write_text(
                'link = "https://youtube.com/c/channel2"\ntarget_folder = "ch2"'
            )
            (channels_dir / "channel3.toml").write_text(
                'link = "https://youtube.com/c/channel3"\ntarget_folder = "ch3"'
            )

            fetcher = ParallelFetcher(conf_file=config_path)
            channel_configs = fetcher.get_channel_configs()
            assert len(channel_configs) == 3


class TestParallelFetcherExecution:
    """Tests for ParallelFetcher.fetch_all() execution."""

    @patch("videos.parallel_fetch.Videos")
    def test_fetch_all_processes_all_channels(self, mock_videos_class):
        """Test that fetch_all processes all channels."""
        from videos.parallel_fetch import ParallelFetcher

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "video_downloads.toml"
            config_path.write_text(
                """
video_definition_dir = "channels"
link_queue_dir = "queue"
target_dir = "downloads"
"""
            )
            channels_dir = Path(tmpdir) / "channels"
            channels_dir.mkdir()
            queue_dir = Path(tmpdir) / "queue"
            queue_dir.mkdir()
            downloads_dir = Path(tmpdir) / "downloads"
            downloads_dir.mkdir()

            # Create channel configs
            (channels_dir / "channel1.toml").write_text(
                'link = "https://youtube.com/c/channel1"\ntarget_folder = "ch1"'
            )
            (channels_dir / "channel2.toml").write_text(
                'link = "https://youtube.com/c/channel2"\ntarget_folder = "ch2"'
            )

            # Mock Videos class to avoid actual yt-dlp calls
            mock_videos_instance = MagicMock()
            mock_videos_instance.write_links.return_value = None
            mock_videos_instance.__len__ = MagicMock(return_value=3)
            mock_videos_instance._conf = {"target_folder": "test"}
            mock_videos_class.return_value = mock_videos_instance

            fetcher = ParallelFetcher(conf_file=config_path, quiet=True)
            results = fetcher.fetch_all()

            assert len(results) == 2
            assert all(r.success for r in results)

    @patch("videos.parallel_fetch.Videos")
    def test_fetch_all_handles_channel_error(self, mock_videos_class):
        """Test that fetch_all continues when one channel fails."""
        from videos.parallel_fetch import ParallelFetcher

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "video_downloads.toml"
            config_path.write_text(
                """
video_definition_dir = "channels"
link_queue_dir = "queue"
target_dir = "downloads"
"""
            )
            channels_dir = Path(tmpdir) / "channels"
            channels_dir.mkdir()
            queue_dir = Path(tmpdir) / "queue"
            queue_dir.mkdir()
            downloads_dir = Path(tmpdir) / "downloads"
            downloads_dir.mkdir()

            # Create channel configs
            (channels_dir / "channel1.toml").write_text(
                'link = "https://youtube.com/c/channel1"\ntarget_folder = "ch1"'
            )
            (channels_dir / "channel2.toml").write_text(
                'link = "https://youtube.com/c/channel2"\ntarget_folder = "ch2"'
            )

            # Mock Videos class - first call succeeds, second fails
            call_count = [0]

            def mock_videos_init(*args, **kwargs):
                call_count[0] += 1
                mock_instance = MagicMock()
                if call_count[0] == 1:
                    mock_instance.write_links.return_value = None
                    mock_instance.__len__ = MagicMock(return_value=2)
                    mock_instance._conf = {"target_folder": "ch1"}
                else:
                    mock_instance.write_links.side_effect = Exception("Network error")
                    mock_instance._conf = {"target_folder": "ch2"}
                return mock_instance

            mock_videos_class.side_effect = mock_videos_init

            fetcher = ParallelFetcher(conf_file=config_path, quiet=True)
            results = fetcher.fetch_all()

            assert len(results) == 2
            # One should succeed, one should fail
            successes = [r for r in results if r.success]
            failures = [r for r in results if not r.success]
            assert len(successes) == 1
            assert len(failures) == 1
            assert failures[0].error is not None


class TestParallelFetcherProgress:
    """Tests for progress display functionality."""

    def test_fetcher_has_progress_attribute(self):
        """Test that ParallelFetcher has progress display capability."""
        from videos.parallel_fetch import ParallelFetcher

        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "video_downloads.toml"
            config_path.write_text(
                """
video_definition_dir = "channels"
link_queue_dir = "queue"
target_dir = "downloads"
"""
            )
            (Path(tmpdir) / "channels").mkdir()
            (Path(tmpdir) / "queue").mkdir()
            (Path(tmpdir) / "downloads").mkdir()

            fetcher = ParallelFetcher(conf_file=config_path)
            # Should have a method to create progress display
            assert hasattr(fetcher, "create_progress")


class TestMainEntryPoint:
    """Tests for the main() entry point function."""

    def test_main_function_exists(self):
        """Test that main entry point function exists."""
        from videos.parallel_fetch import main

        assert callable(main)

    @patch("videos.parallel_fetch.ParallelFetcher")
    def test_main_creates_fetcher_with_defaults(self, mock_fetcher_class):
        """Test that main creates ParallelFetcher with default settings."""
        from videos.parallel_fetch import main

        mock_fetcher = MagicMock()
        mock_fetcher.fetch_all.return_value = []
        mock_fetcher_class.return_value = mock_fetcher

        # Call main with no arguments (uses defaults)
        main()

        mock_fetcher_class.assert_called_once()
        mock_fetcher.fetch_all.assert_called_once()
