import logging

from sqlalchemy.orm import Session

from app import models
from app.core import config
from app.core.security import get_password_hash
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def create_super_admin(db: Session) -> None:
    user = (
        db.query(models.User)
        .filter(models.User.username == config.settings.FIRST_SUPERUSER)
        .first()
    )

    if not user:
        user = models.User(
            username=config.settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(
                config.settings.FIRST_SUPERUSER_PASSWORD
            ),
            is_superuser=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    logger.info("first super user created")


def init_db(db: Session) -> None:
    try:
        create_super_admin(db)
    except Exception as e:
        logger.error(f"initial data creation error\n{e}")


if __name__ == "__main__":
    db = SessionLocal()
    init_db(db)
