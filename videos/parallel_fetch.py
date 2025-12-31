"""Parallel video link fetcher with progress display.

This module provides concurrent video link fetching from multiple channels
using a thread pool, with cargo-style progress display using Rich.
"""

import argparse
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from .main import Main
from .videos import Videos

logger = logging.getLogger(__name__)

# Default number of worker threads for parallel fetching
DEFAULT_FETCH_WORKER_COUNT = 5

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0  # seconds


@dataclass
class ChannelResult:
    """Result of processing a single channel.

    Attributes:
        channel_name: Name of the channel or target folder.
        config_file: Path to the channel's TOML configuration file.
        new_videos: Number of new videos discovered.
        success: Whether the channel was processed successfully.
        error: Error message if processing failed, None otherwise.
        retry_count: Number of retries attempted before success/failure.
        duration: Time in seconds to process this channel.
    """

    channel_name: str
    config_file: Path
    new_videos: int
    success: bool
    error: str | None
    retry_count: int = field(default=0)
    duration: float = field(default=0.0)


class ParallelFetcher:
    """Parallel video link fetcher with progress display.

    Fetches video links from multiple channels concurrently using
    a thread pool, displaying cargo-style progress using Rich.

    Attributes:
        main: Main orchestrator instance.
        worker_count: Number of concurrent worker threads.
        quiet: Whether to suppress progress output.
        max_retries: Maximum number of retry attempts per channel.
        retry_delay: Base delay in seconds between retries (exponential backoff).
    """

    def __init__(
        self,
        conf_file: Path | str = "video_downloads.toml",
        worker_count: int = DEFAULT_FETCH_WORKER_COUNT,
        quiet: bool = False,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
    ):
        """Initialize the parallel fetcher.

        Args:
            conf_file: Path to the main configuration TOML file.
            worker_count: Number of concurrent worker threads.
            quiet: Whether to suppress progress output.
            max_retries: Maximum number of retry attempts per channel.
            retry_delay: Base delay in seconds between retries.
        """
        self.main = Main(conf_file)
        self.worker_count = worker_count
        self.quiet = quiet
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.console = Console(quiet=quiet)
        self._shutdown_requested = False
        self._start_time: float | None = None
        self._elapsed_time: float = 0.0

    def request_shutdown(self) -> None:
        """Request graceful shutdown of the fetcher.

        This will stop processing new channels but allow currently
        running channels to complete.
        """
        self._shutdown_requested = True
        logger.info("Shutdown requested - completing current channels...")

    def get_channel_configs(self) -> list[Path]:
        """Get all channel configuration files.

        Returns:
            List of paths to channel TOML configuration files.
        """
        path = self.main.video_definition_dir
        return list(path.glob("*.toml"))

    def create_progress(self) -> Progress:
        """Create a Rich Progress instance for display.

        Returns:
            Configured Progress instance with cargo-style columns.
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(),
            console=self.console,
            expand=True,
            disable=self.quiet,
        )

    def _process_channel(
        self,
        config_file: Path,
        progress: Progress | None = None,
        task_id: TaskID | None = None,
    ) -> ChannelResult:
        """Process a single channel with retry logic.

        This method runs in a worker thread and implements exponential
        backoff for transient failures.

        Args:
            config_file: Path to the channel's TOML configuration file.
            progress: Optional Progress instance for updates.
            task_id: Optional task ID for progress updates.

        Returns:
            ChannelResult with processing outcome, retry count, and duration.
        """
        start_time = time.monotonic()
        channel_name = config_file.stem
        retry_count = 0
        last_error: str | None = None

        for attempt in range(self.max_retries + 1):
            try:
                # Create Videos instance for this channel
                videos = Videos(
                    config_file,
                    cache_dir=self.main.link_queue_dir,
                    prefix_dir=self.main.target_prefix,
                )

                # Get channel name from config if available
                channel_name = videos._conf.get("target_folder", config_file.stem)

                # Update progress description if available
                if progress and task_id is not None:
                    retry_info = f" (retry {attempt})" if attempt > 0 else ""
                    progress.update(
                        task_id,
                        description=f"[cyan]Fetching: {channel_name}{retry_info}",
                    )

                # Write links for new videos
                videos.write_links()

                # Count new videos
                new_video_count = len(videos)

                duration = time.monotonic() - start_time
                logger.info(
                    "Channel %s: %d new videos (retries: %d, duration: %.2fs)",
                    channel_name,
                    new_video_count,
                    retry_count,
                    duration,
                )

                return ChannelResult(
                    channel_name=channel_name,
                    config_file=config_file,
                    new_videos=new_video_count,
                    success=True,
                    error=None,
                    retry_count=retry_count,
                    duration=duration,
                )

            except Exception as e:
                last_error = str(e)
                retry_count = attempt + 1

                if attempt < self.max_retries:
                    # Calculate exponential backoff delay
                    delay = self.retry_delay * (2**attempt)
                    logger.warning(
                        "Channel %s failed (attempt %d/%d): %s. Retrying in %.1fs...",
                        channel_name,
                        attempt + 1,
                        self.max_retries + 1,
                        e,
                        delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "Channel %s failed after %d attempts: %s",
                        channel_name,
                        self.max_retries + 1,
                        e,
                    )

        # All retries exhausted
        duration = time.monotonic() - start_time
        return ChannelResult(
            channel_name=channel_name,
            config_file=config_file,
            new_videos=0,
            success=False,
            error=last_error,
            retry_count=retry_count,
            duration=duration,
        )

    def fetch_all(self) -> list[ChannelResult]:
        """Fetch links from all channels in parallel.

        Uses a thread pool to process channels concurrently,
        displaying progress using Rich.

        Returns:
            List of ChannelResult objects for each channel.
        """
        self._start_time = time.monotonic()
        channel_configs = self.get_channel_configs()
        results: list[ChannelResult] = []

        if not channel_configs:
            logger.info("No channel configurations found.")
            self._elapsed_time = time.monotonic() - self._start_time
            return results

        if self.quiet:
            # Simple execution without progress display
            with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
                futures = {
                    executor.submit(self._process_channel, config): config
                    for config in channel_configs
                }
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
        else:
            # Execute with progress display
            with self.create_progress() as progress:
                # Add overall progress task
                overall_task = progress.add_task(
                    "[green]Fetching video links...",
                    total=len(channel_configs),
                )

                with ThreadPoolExecutor(max_workers=self.worker_count) as executor:
                    futures = {
                        executor.submit(
                            self._process_channel, config, progress, None
                        ): config
                        for config in channel_configs
                    }

                    for future in as_completed(futures):
                        result = future.result()
                        results.append(result)

                        # Update overall progress
                        progress.advance(overall_task)

                        # Log completion
                        if result.success:
                            progress.console.print(
                                f"[green]✓[/green] {result.channel_name}: "
                                f"{result.new_videos} new videos"
                            )
                        else:
                            progress.console.print(
                                f"[red]✗[/red] {result.channel_name}: {result.error}"
                            )

        # Record elapsed time
        self._elapsed_time = time.monotonic() - self._start_time

        # Print summary
        self._print_summary(results)

        return results

    def get_summary(self, results: list[ChannelResult]) -> dict[str, Any]:
        """Get a summary dictionary of the fetch operation.

        Args:
            results: List of ChannelResult objects.

        Returns:
            Dictionary containing summary statistics.
        """
        total_channels = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total_channels - successful
        total_videos = sum(r.new_videos for r in results)
        total_retries = sum(r.retry_count for r in results)

        failed_channels = [
            {
                "channel_name": r.channel_name,
                "config_file": str(r.config_file),
                "error": r.error,
                "retry_count": r.retry_count,
            }
            for r in results
            if not r.success
        ]

        return {
            "total_channels": total_channels,
            "successful": successful,
            "failed": failed,
            "total_videos": total_videos,
            "total_retries": total_retries,
            "failed_channels": failed_channels,
            "elapsed_time": self._elapsed_time,
        }

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format.

        Args:
            seconds: Duration in seconds.

        Returns:
            Formatted duration string (e.g., "1m 23s" or "45.2s").
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"

    def _print_summary(self, results: list[ChannelResult]) -> None:
        """Print a summary of the fetch operation.

        Args:
            results: List of ChannelResult objects.
        """
        summary = self.get_summary(results)

        if not self.quiet:
            self.console.print()

            # Create summary table
            table = Table(show_header=False, box=None, padding=(0, 1))
            table.add_column("Label", style="bold")
            table.add_column("Value")

            table.add_row(
                "Channels processed:",
                f"{summary['successful']}/{summary['total_channels']}",
            )
            table.add_row("New videos queued:", str(summary["total_videos"]))
            table.add_row(
                "Elapsed time:",
                self._format_duration(summary["elapsed_time"]),
            )

            if summary["total_retries"] > 0:
                table.add_row("Total retries:", str(summary["total_retries"]))

            if summary["failed"] > 0:
                table.add_row(
                    "[yellow]Failed channels:[/yellow]",
                    f"[yellow]{summary['failed']}[/yellow]",
                )

                # Show failed channel details
                for failed in summary["failed_channels"]:
                    table.add_row(
                        f"  [red]• {failed['channel_name']}[/red]",
                        f"[dim]{failed['error']}[/dim]",
                    )

            self.console.print(table)
            self.console.print()


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        args: List of arguments to parse. If None, uses sys.argv.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        prog="fetch_links_parallel",
        description="Fetch video links from all configured channels in parallel.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fetch_links_parallel                    # Use defaults
  fetch_links_parallel -w 10              # Use 10 workers
  fetch_links_parallel -q                 # Quiet mode
  fetch_links_parallel --max-retries 5    # Retry failed channels 5 times
  fetch_links_parallel custom.toml        # Use custom config file
""",
    )

    parser.add_argument(
        "config",
        nargs="?",
        default="video_downloads.toml",
        help="Path to the main configuration file (default: video_downloads.toml)",
    )

    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=DEFAULT_FETCH_WORKER_COUNT,
        help=f"Number of concurrent worker threads (default: {DEFAULT_FETCH_WORKER_COUNT})",
    )

    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress progress output",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=DEFAULT_MAX_RETRIES,
        help=f"Maximum retry attempts per channel (default: {DEFAULT_MAX_RETRIES})",
    )

    return parser.parse_args(args)


def main(
    conf_file: str = "video_downloads.toml",
    worker_count: int = DEFAULT_FETCH_WORKER_COUNT,
    quiet: bool = False,
) -> None:
    """Main entry point for parallel link fetching (programmatic API).

    Args:
        conf_file: Path to the main configuration file.
        worker_count: Number of concurrent worker threads.
        quiet: Whether to suppress progress output.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    fetcher = ParallelFetcher(
        conf_file=conf_file,
        worker_count=worker_count,
        quiet=quiet,
    )
    fetcher.fetch_all()


def cli_main(args: list[str] | None = None) -> None:
    """CLI entry point for parallel link fetching.

    Args:
        args: List of arguments to parse. If None, uses sys.argv.
    """
    parsed = parse_args(args)

    # Configure logging based on quiet mode
    log_level = logging.WARNING if parsed.quiet else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    fetcher = ParallelFetcher(
        conf_file=parsed.config,
        worker_count=parsed.workers,
        quiet=parsed.quiet,
        max_retries=parsed.max_retries,
    )
    fetcher.fetch_all()


if __name__ == "__main__":
    cli_main()
