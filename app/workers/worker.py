import logging

from rq import Connection, Queue, SimpleWorker

from app.config import Config
from app.logging import setup_logging
from app.storage.redis import get_redis_sync


setup_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    config = Config.from_env()
    redis_conn = get_redis_sync(config.redis_url)
    with Connection(redis_conn):
        queue = Queue("default")
        worker = SimpleWorker([queue])
        logger.info("Worker started")
        worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
