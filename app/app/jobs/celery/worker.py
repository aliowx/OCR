from app.core.celery_app import celery_app
import math
from fastapi.encoders import jsonable_encoder
import random
from app import schemas, crud
from app.core.celery_app import DatabaseTask, celery_app
from app.schemas import RecordUpdate, PlateUpdate
import logging



namespace = "parking"
logger = logging.getLogger(__name__)



@celery_app.task(name="app.celery.worker.test_cele")
def test_cele():
    return "mamad"


@celery_app.task(name="app.celery.worker.test_celery")
def test_celery(word: str) -> str:
    return f"test task return {word}"


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    acks_late=True,
    max_retries=4,
    soft_time_limit=240,
    time_limit=360,
    name="app.celery.worker.add_plates",
)
def add_plates(self, plate: dict) -> str:
    logger.info(f"add_plate: {plate['ocr']}")

    try:
        plate = crud.plate.create_plate(db=self.session, obj_in=plate)

        celery_app.send_task(
            "app.worker.update_record",
            args=[plate.id],
        )

    except Exception as exc:
        countdown = int(random.uniform(1, 2) ** self.request.retries)
        logger.info(f"Error adding plate:{exc} ,retrying in {countdown}s.")
        logger.exception(exc)
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    acks_late=True,
    max_retries=3,
    soft_time_limit=240,
    time_limit=360,
)
def update_record(self, plate_id) -> str:
    logger.info(f"******** update_record: {plate_id}")

    if plate_id == {}:
        logger.warning(f"Invalid Plate id found: {plate_id}")
        return None

    if isinstance(plate_id, dict) and "id" in plate_id:
        plate_id = plate_id["id"]

    try:
        # lock plates table to prevent multiple record insertion
        self.session.execute("LOCK TABLE plate IN EXCLUSIVE MODE")
        plate = crud.plate.get(self.session, plate_id)
        # user = crud.user.get(self.session, user["id"])
        record = crud.record.get_by_plate(self.session, plate=plate, for_update=True)

        if record is None:
            # this is a new record
            record = schemas.RecordCreate(
                ocr=plate.ocr,
                record_number=0,
                start_time=plate.record_time,
                end_time=plate.record_time,
                score=0.01,
                best_lpr_id=plate.lpr_id,
                best_big_image_id=plate.big_image_id,
            )
            record = crud.record.create_with_owner(db=self.session, obj_in=record)

        else:

            if record.start_time > plate.record_time:

                record_update = RecordUpdate(
                    score=math.sqrt(record.score),
                    start_time=plate.record_time,
                )
            elif record.end_time < plate.record_time:
                record_update = RecordUpdate(
                    score=math.sqrt(record.score),
                    end_time=plate.record_time,
                    best_lpr_id=plate.lpr_id,
                    best_big_image_id=plate.big_image_id,
                )
            else:
                record_update = RecordUpdate(
                    score=math.sqrt(record.score),
                )

            record = crud.record.update(
                self.session, db_obj=record, obj_in=record_update
            )
            # end of else for update record

        update_plate = PlateUpdate(record_id=record.id)

        # check if new frame has not additional_data. (for manual plate insert)
        plate = crud.plate.update(self.session, db_obj=plate, obj_in=update_plate)

    except Exception as exc:
        countdown = int(random.uniform(2, 4) ** self.request.retries)
        logger.info(f"Error adding record:{exc} ,retring in {countdown}s.")
        logger.exception(exc)
        raise self.retry(exc=exc, countdown=countdown)
