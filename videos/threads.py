import logging
from pathlib import Path
from queue import Queue
from threading import Thread
from time import time

from videos.functions import Main, download_link  # setup_download_dir, get_links, download_link

# Template from https://www.toptal.com/python/beginners-guide-to-concurrency-and-parallelism-in-python

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)


class DownloadWorker(Thread):

    def __init__(self, queue):
        Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # Get the work from the queue and expand the tuple
            directory, link = self.queue.get()
            try:
                download_link(link, directory)
            finally:
                self.queue.task_done()


def main(worker_count: int = 3, conf_file: Path | str = "video_downloads.toml"):
    m = Main(conf_file)
    path = m.link_queue_dir
    download_dir = m.target_prefix
    links = [json_file for json_file in path.glob('*.json')]

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
        logger.info('Queueing {}'.format(link))
        queue.put((download_dir, link))
    # Causes the main thread to wait for the queue to finish processing all the tasks
    queue.join()
    logging.info('Took %s', time() - ts)


if __name__ == '__main__':
    main(conf_file="../video_downloads.toml")
