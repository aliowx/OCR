import logging

import redis
from tenacity import (
    after_log,
    before_log,
    retry,
    stop_after_attempt,
    wait_fixed,
)

from app.core.config import settings
from cache.redis import redis_connect_sync

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redis_client = redis_connect_sync()

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init() -> None:
    try:
        # Try to create session to check if DB is awake
        # sess = SessionLocal()
        # sess.execute("SELECT 1")
        # sess.close()

        # Try to create session to check if redis is awake
        # client = redis.Redis(
        #     host=settings.REDIS_SERVER,
        #     port=settings.REDIS_PORT,
        #     password=settings.REDIS_PASSWORD,
        #     db=settings.REDIS_DB,
        #     socket_timeout=settings.REDIS_TIMEOUT,
        #     decode_responses=False,
        # )
        client = redis.from_url(str(settings.REDIS_URI))
        ping = client.ping()
        if not ping:
            raise Exception("No redis ping...")
    except Exception as e:
        logger.error("celery")
        logger.exception(e)
        logger.error(e)
        raise e


def main() -> None:
    logger.info("Initializing service")
    init()
    logger.info("Service finished initializing")


if __name__ == "__main__":
    main()
