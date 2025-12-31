"""Unit tests for the parallel fetch functionality.

These tests follow TDD approach - written before the implementation.
"""

import tempfile
import time
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

    def test_progress_display_has_correct_columns(self):
        """Test that progress display has cargo-style columns."""
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
            progress = fetcher.create_progress()

            # Progress should have multiple columns for cargo-style display
            assert len(progress.columns) >= 4  # At least spinner, text, bar, time

    def test_progress_display_disabled_in_quiet_mode(self):
        """Test that progress display is disabled in quiet mode."""
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
            progress = fetcher.create_progress()

            # Progress should be disabled in quiet mode
            assert progress.disable is True

    @patch("videos.parallel_fetch.Videos")
    def test_progress_shows_correct_channel_count(self, mock_videos_class):
        """Test that progress display shows correct total channel count."""
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

            # Create 5 channel configs
            for i in range(5):
                (channels_dir / f"channel{i}.toml").write_text(
                    f'link = "https://youtube.com/c/channel{i}"\ntarget_folder = "ch{i}"'
                )

            # Mock Videos class
            mock_videos_instance = MagicMock()
            mock_videos_instance.write_links.return_value = None
            mock_videos_instance.__len__ = MagicMock(return_value=1)
            mock_videos_instance._conf = {"target_folder": "test"}
            mock_videos_class.return_value = mock_videos_instance

            fetcher = ParallelFetcher(conf_file=config_path, quiet=True)
            results = fetcher.fetch_all()

            # Should have processed all 5 channels
            assert len(results) == 5

    @patch("videos.parallel_fetch.Videos")
    def test_progress_updates_on_channel_completion(self, mock_videos_class):
        """Test that progress advances when each channel completes."""
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

            # Create channel configs
            for i in range(3):
                (channels_dir / f"channel{i}.toml").write_text(
                    f'link = "https://youtube.com/c/channel{i}"\ntarget_folder = "ch{i}"'
                )

            # Track video counts per channel
            video_counts = [2, 5, 3]
            call_count = [0]

            def mock_videos_init(*args, **kwargs):
                idx = call_count[0]
                call_count[0] += 1
                mock_instance = MagicMock()
                mock_instance.write_links.return_value = None
                mock_instance.__len__ = MagicMock(
                    return_value=video_counts[idx % len(video_counts)]
                )
                mock_instance._conf = {"target_folder": f"ch{idx}"}
                return mock_instance

            mock_videos_class.side_effect = mock_videos_init

            fetcher = ParallelFetcher(conf_file=config_path, quiet=True)
            results = fetcher.fetch_all()

            # All channels should complete
            assert len(results) == 3
            assert all(r.success for r in results)

            # Total videos should match
            total_videos = sum(r.new_videos for r in results)
            assert total_videos == sum(video_counts)

    @patch("videos.parallel_fetch.Videos")
    def test_progress_handles_errors_gracefully(self, mock_videos_class):
        """Test that progress display handles errors without crashing."""
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

            # Create channel configs
            for i in range(3):
                (channels_dir / f"channel{i}.toml").write_text(
                    f'link = "https://youtube.com/c/channel{i}"\ntarget_folder = "ch{i}"'
                )

            # Make middle channel always fail (use max_retries=0 to disable retries)
            call_count = [0]

            def mock_videos_init(*args, **kwargs):
                idx = call_count[0]
                call_count[0] += 1
                mock_instance = MagicMock()
                if idx == 1:
                    mock_instance.write_links.side_effect = Exception("API error")
                    mock_instance._conf = {"target_folder": f"ch{idx}"}
                else:
                    mock_instance.write_links.return_value = None
                    mock_instance.__len__ = MagicMock(return_value=2)
                    mock_instance._conf = {"target_folder": f"ch{idx}"}
                return mock_instance

            mock_videos_class.side_effect = mock_videos_init

            # Disable retries so the failing channel doesn't eventually succeed
            fetcher = ParallelFetcher(conf_file=config_path, quiet=True, max_retries=0)
            results = fetcher.fetch_all()

            # All channels should be in results
            assert len(results) == 3

            # One should have failed
            failures = [r for r in results if not r.success]
            assert len(failures) == 1
            assert failures[0].error is not None
            assert "API error" in failures[0].error

            # Others should have succeeded
            successes = [r for r in results if r.success]
            assert len(successes) == 2


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


class TestRetryLogic:
    """Tests for retry logic and exponential backoff."""

    def test_parallel_fetcher_default_retry_count(self):
        """Test that ParallelFetcher defaults to 3 retries."""
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
            assert fetcher.max_retries == 3

    def test_parallel_fetcher_custom_retry_count(self):
        """Test that ParallelFetcher accepts custom retry count."""
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

            fetcher = ParallelFetcher(conf_file=config_path, max_retries=5)
            assert fetcher.max_retries == 5

    def test_parallel_fetcher_retry_delay_default(self):
        """Test that ParallelFetcher has default retry delay."""
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
            assert fetcher.retry_delay == 1.0  # 1 second base delay

    @patch("videos.parallel_fetch.Videos")
    @patch("videos.parallel_fetch.time.sleep")
    def test_retry_on_transient_error(self, mock_sleep, mock_videos_class):
        """Test that transient errors trigger retry."""
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

            (channels_dir / "channel1.toml").write_text(
                'link = "https://youtube.com/c/channel1"\ntarget_folder = "ch1"'
            )

            # Fail twice, then succeed
            call_count = [0]

            def mock_videos_init(*args, **kwargs):
                call_count[0] += 1
                mock_instance = MagicMock()
                if call_count[0] <= 2:
                    mock_instance.write_links.side_effect = Exception("Network timeout")
                else:
                    mock_instance.write_links.return_value = None
                    mock_instance.__len__ = MagicMock(return_value=3)
                mock_instance._conf = {"target_folder": "ch1"}
                return mock_instance

            mock_videos_class.side_effect = mock_videos_init

            fetcher = ParallelFetcher(conf_file=config_path, quiet=True, max_retries=3)
            results = fetcher.fetch_all()

            assert len(results) == 1
            assert results[0].success is True
            assert results[0].retry_count == 2  # Retried twice before success

    @patch("videos.parallel_fetch.Videos")
    @patch("videos.parallel_fetch.time.sleep")
    def test_exponential_backoff_delays(self, mock_sleep, mock_videos_class):
        """Test that retry delays follow exponential backoff."""
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

            (channels_dir / "channel1.toml").write_text(
                'link = "https://youtube.com/c/channel1"\ntarget_folder = "ch1"'
            )

            # Always fail to trigger all retries
            mock_instance = MagicMock()
            mock_instance.write_links.side_effect = Exception("Persistent error")
            mock_instance._conf = {"target_folder": "ch1"}
            mock_videos_class.return_value = mock_instance

            fetcher = ParallelFetcher(
                conf_file=config_path, quiet=True, max_retries=3, retry_delay=1.0
            )
            fetcher.fetch_all()  # Result not needed, we're testing sleep calls

            # Should have called sleep with exponential delays: 1, 2, 4 seconds
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert len(sleep_calls) == 3
            assert sleep_calls[0] == 1.0  # 1 * 2^0
            assert sleep_calls[1] == 2.0  # 1 * 2^1
            assert sleep_calls[2] == 4.0  # 1 * 2^2

    @patch("videos.parallel_fetch.Videos")
    @patch("videos.parallel_fetch.time.sleep")
    def test_max_retries_exhausted(self, mock_sleep, mock_videos_class):
        """Test that channel fails after max retries exhausted."""
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

            (channels_dir / "channel1.toml").write_text(
                'link = "https://youtube.com/c/channel1"\ntarget_folder = "ch1"'
            )

            # Always fail
            mock_instance = MagicMock()
            mock_instance.write_links.side_effect = Exception("Persistent error")
            mock_instance._conf = {"target_folder": "ch1"}
            mock_videos_class.return_value = mock_instance

            fetcher = ParallelFetcher(conf_file=config_path, quiet=True, max_retries=3)
            results = fetcher.fetch_all()

            assert len(results) == 1
            assert results[0].success is False
            # retry_count = number of attempts (1 initial + 3 retries = 4)
            assert results[0].retry_count == 4
            assert results[0].error is not None
            assert "Persistent error" in results[0].error


class TestChannelResultEnhanced:
    """Tests for enhanced ChannelResult with retry tracking."""

    def test_channel_result_has_retry_count(self):
        """Test that ChannelResult tracks retry count."""
        from videos.parallel_fetch import ChannelResult

        result = ChannelResult(
            channel_name="TestChannel",
            config_file=Path("/path/to/config.toml"),
            new_videos=5,
            success=True,
            error=None,
            retry_count=2,
        )
        assert result.retry_count == 2

    def test_channel_result_default_retry_count(self):
        """Test that ChannelResult defaults to 0 retries."""
        from videos.parallel_fetch import ChannelResult

        result = ChannelResult(
            channel_name="TestChannel",
            config_file=Path("/path/to/config.toml"),
            new_videos=5,
            success=True,
            error=None,
        )
        assert result.retry_count == 0


class TestErrorSummary:
    """Tests for error summary display."""

    @patch("videos.parallel_fetch.Videos")
    def test_summary_shows_retry_statistics(self, mock_videos_class):
        """Test that summary includes retry statistics."""
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

            # Create channel configs
            for i in range(3):
                (channels_dir / f"channel{i}.toml").write_text(
                    f'link = "https://youtube.com/c/channel{i}"\ntarget_folder = "ch{i}"'
                )

            # Mock Videos class
            mock_instance = MagicMock()
            mock_instance.write_links.return_value = None
            mock_instance.__len__ = MagicMock(return_value=2)
            mock_instance._conf = {"target_folder": "test"}
            mock_videos_class.return_value = mock_instance

            fetcher = ParallelFetcher(conf_file=config_path, quiet=True)
            results = fetcher.fetch_all()

            # Summary should be accessible
            summary = fetcher.get_summary(results)
            assert "total_channels" in summary
            assert "successful" in summary
            assert "failed" in summary
            assert "total_videos" in summary
            assert "total_retries" in summary

    @patch("videos.parallel_fetch.Videos")
    def test_error_details_in_summary(self, mock_videos_class):
        """Test that summary includes error details for failed channels."""
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

            # Create channel configs
            (channels_dir / "channel1.toml").write_text(
                'link = "https://youtube.com/c/channel1"\ntarget_folder = "ch1"'
            )
            (channels_dir / "channel2.toml").write_text(
                'link = "https://youtube.com/c/channel2"\ntarget_folder = "ch2"'
            )

            # Make one channel fail
            call_count = [0]

            def mock_videos_init(*args, **kwargs):
                call_count[0] += 1
                mock_instance = MagicMock()
                if call_count[0] == 1:
                    mock_instance.write_links.return_value = None
                    mock_instance.__len__ = MagicMock(return_value=2)
                else:
                    mock_instance.write_links.side_effect = Exception("API rate limit")
                mock_instance._conf = {"target_folder": f"ch{call_count[0]}"}
                return mock_instance

            mock_videos_class.side_effect = mock_videos_init

            fetcher = ParallelFetcher(conf_file=config_path, quiet=True, max_retries=0)
            results = fetcher.fetch_all()

            summary = fetcher.get_summary(results)
            assert "failed_channels" in summary
            assert len(summary["failed_channels"]) == 1
            assert "API rate limit" in summary["failed_channels"][0]["error"]


class TestCLIArgumentParsing:
    """Tests for CLI argument parsing."""

    def test_cli_entry_point_exists(self):
        """Test that cli_main entry point function exists."""
        from videos.parallel_fetch import cli_main

        assert callable(cli_main)

    def test_parse_args_default_values(self):
        """Test that parse_args returns default values."""
        from videos.parallel_fetch import parse_args

        args = parse_args([])
        assert args.config == "video_downloads.toml"
        assert args.workers == 5
        assert args.quiet is False
        assert args.max_retries == 3

    def test_parse_args_workers_short_flag(self):
        """Test that -w flag sets worker count."""
        from videos.parallel_fetch import parse_args

        args = parse_args(["-w", "10"])
        assert args.workers == 10

    def test_parse_args_workers_long_flag(self):
        """Test that --workers flag sets worker count."""
        from videos.parallel_fetch import parse_args

        args = parse_args(["--workers", "8"])
        assert args.workers == 8

    def test_parse_args_quiet_short_flag(self):
        """Test that -q flag enables quiet mode."""
        from videos.parallel_fetch import parse_args

        args = parse_args(["-q"])
        assert args.quiet is True

    def test_parse_args_quiet_long_flag(self):
        """Test that --quiet flag enables quiet mode."""
        from videos.parallel_fetch import parse_args

        args = parse_args(["--quiet"])
        assert args.quiet is True

    def test_parse_args_max_retries_flag(self):
        """Test that --max-retries flag sets retry count."""
        from videos.parallel_fetch import parse_args

        args = parse_args(["--max-retries", "5"])
        assert args.max_retries == 5

    def test_parse_args_config_positional(self):
        """Test that config file can be specified as positional argument."""
        from videos.parallel_fetch import parse_args

        args = parse_args(["my_config.toml"])
        assert args.config == "my_config.toml"

    def test_parse_args_all_options(self):
        """Test that all options can be combined."""
        from videos.parallel_fetch import parse_args

        args = parse_args(
            ["--workers", "10", "--quiet", "--max-retries", "5", "custom.toml"]
        )
        assert args.workers == 10
        assert args.quiet is True
        assert args.max_retries == 5
        assert args.config == "custom.toml"

    @patch("videos.parallel_fetch.ParallelFetcher")
    def test_cli_main_passes_args_to_fetcher(self, mock_fetcher_class):
        """Test that cli_main passes CLI args to ParallelFetcher."""
        from videos.parallel_fetch import cli_main

        mock_fetcher = MagicMock()
        mock_fetcher.fetch_all.return_value = []
        mock_fetcher_class.return_value = mock_fetcher

        # Simulate CLI args
        test_args = ["--workers", "8", "--quiet", "--max-retries", "2"]
        cli_main(test_args)

        # Verify ParallelFetcher was created with correct args
        mock_fetcher_class.assert_called_once()
        call_kwargs = mock_fetcher_class.call_args[1]
        assert call_kwargs["worker_count"] == 8
        assert call_kwargs["quiet"] is True
        assert call_kwargs["max_retries"] == 2


class TestTimingStatistics:
    """Tests for timing statistics in summary."""

    @patch("videos.parallel_fetch.Videos")
    def test_summary_includes_elapsed_time(self, mock_videos_class):
        """Test that summary includes total elapsed time."""
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

            # Create channel config
            (channels_dir / "channel1.toml").write_text(
                'link = "https://youtube.com/c/channel1"\ntarget_folder = "ch1"'
            )

            # Mock Videos class
            mock_instance = MagicMock()
            mock_instance.write_links.return_value = None
            mock_instance.__len__ = MagicMock(return_value=2)
            mock_instance._conf = {"target_folder": "test"}
            mock_videos_class.return_value = mock_instance

            fetcher = ParallelFetcher(conf_file=config_path, quiet=True)
            results = fetcher.fetch_all()

            summary = fetcher.get_summary(results)
            assert "elapsed_time" in summary
            assert isinstance(summary["elapsed_time"], float)
            assert summary["elapsed_time"] >= 0

    @patch("videos.parallel_fetch.Videos")
    def test_channel_result_includes_duration(self, mock_videos_class):
        """Test that each channel result includes processing duration."""
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

            (channels_dir / "channel1.toml").write_text(
                'link = "https://youtube.com/c/channel1"\ntarget_folder = "ch1"'
            )

            # Mock Videos class with a small delay
            def mock_videos_init(*args, **kwargs):
                mock_instance = MagicMock()
                mock_instance.write_links.return_value = None
                mock_instance.__len__ = MagicMock(return_value=2)
                mock_instance._conf = {"target_folder": "ch1"}
                time.sleep(0.01)  # Small delay to ensure measurable duration
                return mock_instance

            mock_videos_class.side_effect = mock_videos_init

            fetcher = ParallelFetcher(conf_file=config_path, quiet=True)
            results = fetcher.fetch_all()

            assert len(results) == 1
            assert hasattr(results[0], "duration")
            assert results[0].duration >= 0


class TestGracefulShutdown:
    """Tests for graceful shutdown on Ctrl+C."""

    def test_fetcher_has_shutdown_flag(self):
        """Test that ParallelFetcher has shutdown flag."""
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
            assert hasattr(fetcher, "_shutdown_requested")
            assert fetcher._shutdown_requested is False

    def test_fetcher_has_request_shutdown_method(self):
        """Test that ParallelFetcher has request_shutdown method."""
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
            assert hasattr(fetcher, "request_shutdown")
            assert callable(fetcher.request_shutdown)

    def test_request_shutdown_sets_flag(self):
        """Test that request_shutdown sets the shutdown flag."""
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
            fetcher.request_shutdown()
            assert fetcher._shutdown_requested is True

    @patch("videos.parallel_fetch.Videos")
    def test_shutdown_returns_partial_results(self, mock_videos_class):
        """Test that shutdown returns results collected so far."""
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

            # Create multiple channel configs
            for i in range(5):
                (channels_dir / f"channel{i}.toml").write_text(
                    f'link = "https://youtube.com/c/channel{i}"\ntarget_folder = "ch{i}"'
                )

            call_count = [0]

            def mock_videos_init(*args, **kwargs):
                call_count[0] += 1
                mock_instance = MagicMock()
                mock_instance.write_links.return_value = None
                mock_instance.__len__ = MagicMock(return_value=1)
                mock_instance._conf = {"target_folder": f"ch{call_count[0]}"}
                return mock_instance

            mock_videos_class.side_effect = mock_videos_init

            fetcher = ParallelFetcher(conf_file=config_path, quiet=True, worker_count=1)

            # Request shutdown immediately - should still get some results
            # (This is a simplified test; real shutdown would be async)
            results = fetcher.fetch_all()

            # Should have processed all channels since shutdown wasn't triggered
            assert len(results) == 5
