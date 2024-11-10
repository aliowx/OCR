import logging

from app.db.init_data_fake import init_db_fake_data
from app.db.session import AsyncSessionLocal
from app.core.config import settings
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init() -> None:
    db = AsyncSessionLocal()
    await init_db_fake_data(db)


async def main() -> None:
    logger.info("Creating initial data")
    await init()
    logger.info("Initial data created")


if __name__ == "__main__":
    if settings.DATA_FAKE_SET:
        asyncio.run(main())
    else:
        print("varibale DATA_FAKE_SET True")
