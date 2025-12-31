"""Parallel video link fetcher with progress display.

This module provides concurrent video link fetching from multiple channels
using a thread pool, with cargo-style progress display using Rich.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from .main import Main
from .videos import Videos

logger = logging.getLogger(__name__)

# Default number of worker threads for parallel fetching
DEFAULT_FETCH_WORKER_COUNT = 5


@dataclass
class ChannelResult:
    """Result of processing a single channel.

    Attributes:
        channel_name: Name of the channel or target folder.
        config_file: Path to the channel's TOML configuration file.
        new_videos: Number of new videos discovered.
        success: Whether the channel was processed successfully.
        error: Error message if processing failed, None otherwise.
    """

    channel_name: str
    config_file: Path
    new_videos: int
    success: bool
    error: str | None


class ParallelFetcher:
    """Parallel video link fetcher with progress display.

    Fetches video links from multiple channels concurrently using
    a thread pool, displaying cargo-style progress using Rich.

    Attributes:
        main: Main orchestrator instance.
        worker_count: Number of concurrent worker threads.
        quiet: Whether to suppress progress output.
    """

    def __init__(
        self,
        conf_file: Path | str = "video_downloads.toml",
        worker_count: int = DEFAULT_FETCH_WORKER_COUNT,
        quiet: bool = False,
    ):
        """Initialize the parallel fetcher.

        Args:
            conf_file: Path to the main configuration TOML file.
            worker_count: Number of concurrent worker threads.
            quiet: Whether to suppress progress output.
        """
        self.main = Main(conf_file)
        self.worker_count = worker_count
        self.quiet = quiet

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
            TimeElapsedColumn(),
            disable=self.quiet,
        )

    def _process_channel(
        self,
        config_file: Path,
        progress: Progress | None = None,
        task_id: TaskID | None = None,
    ) -> ChannelResult:
        """Process a single channel - fetch and write links.

        This method runs in a worker thread.

        Args:
            config_file: Path to the channel's TOML configuration file.
            progress: Optional Progress instance for updates.
            task_id: Optional task ID for progress updates.

        Returns:
            ChannelResult with processing outcome.
        """
        channel_name = config_file.stem
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
                progress.update(
                    task_id,
                    description=f"[cyan]Fetching: {channel_name}",
                )

            # Write links for new videos
            videos.write_links()

            # Count new videos
            new_video_count = len(videos)

            logger.info(
                "Channel %s: %d new videos",
                channel_name,
                new_video_count,
            )

            return ChannelResult(
                channel_name=channel_name,
                config_file=config_file,
                new_videos=new_video_count,
                success=True,
                error=None,
            )

        except Exception as e:
            logger.error("Failed to process channel %s: %s", channel_name, e)
            return ChannelResult(
                channel_name=channel_name,
                config_file=config_file,
                new_videos=0,
                success=False,
                error=str(e),
            )

    def fetch_all(self) -> list[ChannelResult]:
        """Fetch links from all channels in parallel.

        Uses a thread pool to process channels concurrently,
        displaying progress using Rich.

        Returns:
            List of ChannelResult objects for each channel.
        """
        channel_configs = self.get_channel_configs()
        results: list[ChannelResult] = []

        if not channel_configs:
            logger.info("No channel configurations found.")
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

        # Print summary
        self._print_summary(results)

        return results

    def _print_summary(self, results: list[ChannelResult]) -> None:
        """Print a summary of the fetch operation.

        Args:
            results: List of ChannelResult objects.
        """
        total_channels = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total_channels - successful
        total_videos = sum(r.new_videos for r in results)

        if not self.quiet:
            print()
            print(
                f"Completed: {successful}/{total_channels} channels, "
                f"{total_videos} new videos queued"
            )
            if failed > 0:
                print(f"[yellow]Warning: {failed} channel(s) failed[/yellow]")


def main(
    conf_file: str = "video_downloads.toml",
    worker_count: int = DEFAULT_FETCH_WORKER_COUNT,
    quiet: bool = False,
) -> None:
    """Main entry point for parallel link fetching.

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


if __name__ == "__main__":
    main()
