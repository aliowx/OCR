import json
import logging

from sqlalchemy.orm import Session

from app import crud, models
from app.core import config
from app.core.security import get_password_hash
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def create_super_admin(db: Session) -> None:
    user = (
        db.query(models.User)
        .filter(models.User.email == config.settings.FIRST_SUPERUSER)
        .first()
    )

    if not user:
        user = models.User(
            email=config.settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(
                config.settings.FIRST_SUPERUSER_PASSWORD
            ),
            is_superuser=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    logger.info("first super user created")


def add_location_date(db: Session) -> None:
    if not crud.province.count(db):
        try:
            with open(
                config.STATIC_DIR / "location/iran/provinces.json", "r"
            ) as province_data:
                provinces = json.load(province_data)
                for p in provinces:
                    crud.province.create(
                        db,
                        obj_in={
                            "name_fa": p["name"],
                            "pid": p["id"],
                        },
                        commit=False,
                    )
                db.commit()
        except FileNotFoundError as e:
            logger.error(
                "Province data not found, add provinces.json file to app/static/location/iran"
            )
            raise e

    if not crud.city.count(db):
        try:
            with open(
                config.STATIC_DIR / "location/iran/cities.json", "r"
            ) as city_data:
                cities = json.load(city_data)
                for c in cities:
                    crud.city.create(
                        db,
                        obj_in={
                            "name_fa": c["name"],
                            "cid": c["id"],
                            "province_id": c["province_id"],
                        },
                        commit=False,
                    )
                db.commit()
        except FileNotFoundError as e:
            logger.error(
                "City data not found, add cities.json file to app/static/location/iran"
            )
            raise e


def init_db(db: Session) -> None:
    try:
        create_super_admin(db)
        add_location_date(db)
    except Exception as e:
        logger.error(f"initial data creation error\n{e}")


if __name__ == "__main__":
    db = SessionLocal()
    init_db(db)
