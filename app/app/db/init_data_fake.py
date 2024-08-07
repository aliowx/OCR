import logging

from sqlalchemy.orm import Session
from app import crud
from app import models
from app.core.fake_data import fake_data
from app.db.session import SessionLocal
from app import schemas
import random
import string
from app.core.celery_app import celery_app
from fastapi.encoders import jsonable_encoder


logger = logging.getLogger(__name__)


def commit_to_db(db: Session, data: any, name: str):
    db.add(data)
    db.commit()
    db.refresh(data)

    logger.info(f"create {name}")

    return data


def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    random_string = "".join(random.choice(characters) for i in range(length))
    return random_string


def create_parking(db: Session) -> None:
    parking = db.query(models.Parking).first()

    if not parking:
        parking = fake_data.PARKING
        commit_to_db(db, data=parking, name="parking")
    return parking


def create_equipment(db: Session):
    equipment = (
        db.query(models.Equipment)
        .where(
            models.Equipment.is_deleted == False,
            models.Equipment.serial_number
            == fake_data.EQUIPMENT.serial_number,
        )
        .first()
    )
    if not equipment:
        equipment = fake_data.EQUIPMENT
        equipment.zone_id = create_zone(db).id
        commit_to_db(db, data=equipment, name="equipment")
    return equipment


def create_image(db: Session):
    image = fake_data.IMAGE
    return commit_to_db(db, data=image, name="image")


def create_zone(db: Session):
    zone = (
        db.query(models.Zone)
        .where(
            models.Zone.is_deleted == False,
            models.Zone.name == fake_data.ZONE.name,
        )
        .first()
    )
    if not zone:
        zone = fake_data.ZONE
        commit_to_db(db, data=zone, name="zone")
    return zone


def create_sub_zone(db: Session):
    sub_zone = (
        db.query(models.Zone)
        .where(
            models.Zone.is_deleted == False,
            models.Zone.name == fake_data.SUB_ZONE.name,
        )
        .first()
    )
    if not sub_zone:
        sub_zone = fake_data.SUB_ZONE
        sub_zone.parent_id = create_zone(db).id
        commit_to_db(db, data=sub_zone, name="sub_zone")
    return sub_zone


def create_records(db: Session):
    records_data = [
        fake_data.RECORD1,
        fake_data.RECORD2,
        fake_data.RECORD_PAST,
    ]
    for record in records_data:
        query_record = (
            db.query(models.Record)
            .where(
                models.Record.is_deleted == False,
                models.Record.plate == record.plate,
            )
            .first()
        )
        if not query_record:
            image = create_image(db)
            record.best_lpr_image_id = image.id
            record.best_plate_image_id = image.id
            record.zone_id = create_zone(db).id
            commit_to_db(db, data=record, name="record")
    return record


def create_plates(db: Session):
    plates_data = [fake_data.PLATE1, fake_data.PLATE2]
    for i in range(1, 10):
        plate = random.choice(plates_data)
        image = create_image(db)
        camera = create_equipment(db)
        zone = create_zone(db)
        if i == 9 or i == 8:
            plate.type_camera = schemas.plate.TypeCamera.exitDoor.value
        plate.plate_image_id = image.id
        plate.lpr_image_id = image.id
        plate.camera_id = camera.id
        plate.zone_id = zone.id
        celery_app.send_task(
            "add_plates",
            args=[jsonable_encoder(plate)],
        )


def init_db_fake_data(db: Session) -> None:
    try:
        create_parking(db)
        create_equipment(db)
        create_image(db)
        create_zone(db)
        create_sub_zone(db)
        create_records(db)
        create_plates(db)
    except Exception as e:
        logger.error(f"initial data creation error\n{e}")


if __name__ == "__main__":
    db = SessionLocal()
    init_db_fake_data(db)
