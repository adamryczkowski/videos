"""Multi-threaded video download module.

This module provides concurrent video downloading using a thread pool
and work queue pattern.

Template from https://www.toptal.com/python/beginners-guide-to-concurrency-and-parallelism-in-python
"""

import logging
from pathlib import Path
from queue import Queue
from threading import Thread
from time import time

from .functions import Main  # setup_download_dir, get_links, download_link
from .main import download_link

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class DownloadWorker(Thread):
    """Worker thread for processing video downloads from a queue.

    Runs as a daemon thread, continuously pulling download tasks
    from the queue until the program exits.

    Attributes:
        queue: Queue containing (directory, link_path) tuples.
    """

    def __init__(self, queue):
        """Initialize the download worker.

        Args:
            queue: Queue to pull download tasks from.
        """
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        """Process downloads from the queue indefinitely.

        Pulls (directory, link) tuples from the queue and downloads
        each video. Marks tasks as done regardless of success/failure.
        Logs errors and skips missing files gracefully.
        """
        while True:
            # Get the work from the queue and expand the tuple
            directory, link = self.queue.get()
            try:
                link_path = Path(link)
                if not link_path.exists():
                    logger.warning("Link file no longer exists: %s", link)
                    continue
                download_link(link_path, directory)
            except Exception as e:
                logger.error("Failed to download %s: %s", link, e)
            finally:
                self.queue.task_done()


def main(worker_count: int = 3, conf_file: Path | str = "video_downloads.toml"):
    """Download all queued videos using multiple worker threads.

    Creates a pool of daemon worker threads that process downloads
    concurrently from a shared queue.

    Args:
        worker_count: Number of concurrent download workers. Defaults to 3.
        conf_file: Path to the main configuration file.
    """
    m = Main(conf_file)
    path = m.link_queue_dir
    download_dir = m.target_prefix
    links = [json_file for json_file in path.glob("*.link")]

    ts = time()

    # Create a queue to communicate with the worker threads
    queue = Queue()
    # Create 8 worker threads
    for x in range(worker_count):
        worker = DownloadWorker(queue)
        # Setting daemon to True will let the main thread exit even though the workers are blocking
        worker.daemon = True
        worker.start()
    # Put the tasks into the queue as a tuple
    for link in links:
        logger.info("Queueing {}".format(link))
        queue.put((download_dir, link))
    # Causes the main thread to wait for the queue to finish processing all the tasks
    queue.join()
    logging.info("Took %s", time() - ts)


if __name__ == "__main__":
    main(conf_file="video_downloads.toml")
