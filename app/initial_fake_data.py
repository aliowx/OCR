import logging

from app.db.init_data_fake import init_db_fake_data
from app.db.session import SessionLocal
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init() -> None:
    db = SessionLocal()
    init_db_fake_data(db)


def main() -> None:
    logger.info("Creating initial data")
    init()
    logger.info("Initial data created")


if __name__ == "__main__":
    if settings.DATA_FAKE_SET:
        main()
    else:
        print("varibale DATA_FAKE_SET True")
