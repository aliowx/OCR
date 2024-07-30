import logging
import math
import random
from datetime import datetime, timedelta, timezone
from sqlalchemy import text

from app import crud, models, schemas
from app.core.celery_app import DatabaseTask, celery_app
from app.core.config import settings
from app.jobs.celery.celeryworker_pre_start import redis_client
from app.schemas import PlateUpdate, RecordUpdate, TypeCamera, StatusRecord

namespace = "job worker"
logger = logging.getLogger(__name__)


@celery_app.task
def test_celery(word: str) -> str:
    return f"test task return {word}"


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    acks_late=True,
    max_retries=4,
    soft_time_limit=240,
    time_limit=360,
    name="add_plates",
)
def add_plates(self, plate: dict) -> str:

    try:
        plate = crud.plate.create(db=self.session, obj_in=plate)

        celery_app.send_task(
            "update_record",
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
    name="update_record",
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
        self.session.execute(text("LOCK TABLE plate IN EXCLUSIVE MODE"))
        plate = crud.plate.get(self.session, plate_id)
        record = crud.record.get_by_plate(
            db=self.session,
            plate=plate,
            status=StatusRecord.unfinished,
            for_update=True,
        )
        if record is None and plate.type_camera != TypeCamera.exitDoor.value:
            record = schemas.RecordCreate(
                plate=plate.plate,
                start_time=plate.record_time,
                end_time=plate.record_time,
                score=0.01,
                best_lpr_image_id=plate.lpr_image_id,
                best_plate_image_id=plate.plate_image_id,
                price_model_id=plate.price_model_id,
                spot_id=plate.spot_id,
                zone_id=plate.zone_id,
                latest_status=StatusRecord.unfinished.value,
            )
            record = crud.record.create(db=self.session, obj_in=record)
        elif record:
            if record.start_time > plate.record_time:
                record_update = RecordUpdate(
                    score=math.sqrt(record.score),
                    start_time=plate.record_time,
                    latest_status=(
                        StatusRecord.finished.value
                        if plate.type_camera == TypeCamera.exitDoor.value
                        else StatusRecord.unfinished.value
                    ),
                )
            elif record.end_time < plate.record_time:
                record_update = RecordUpdate(
                    score=math.sqrt(record.score),
                    end_time=plate.record_time,
                    best_lpr_image_id=plate.lpr_image_id,
                    best_plate_image_id=plate.plate_image_id,
                    latest_status=(
                        StatusRecord.finished.value
                        if plate.type_camera == TypeCamera.exitDoor.value
                        else StatusRecord.unfinished.value
                    ),
                )
            else:
                record_update = RecordUpdate(
                    score=math.sqrt(record.score),
                    latest_status=(
                        StatusRecord.finished.value
                        if plate.type_camera == TypeCamera.exitDoor.value
                        else StatusRecord.unfinished.value
                    ),
                )

            record = crud.record.update(
                self.session, db_obj=record, obj_in=record_update
            )

            update_plate = PlateUpdate(record_id=record.id)
            # this refresh for update plate with out this not working ==> solution 1
            self.session.refresh(plate)
            # or solution 2
            # logger.info(f"latest value plate.record_id ===> {plate.record_id}")
            # or solution 3
            # plate.record_id = record.id
            # plate_update = crud.plate.update(
            #     self.session, db_obj=plate
            # )

            plate_update = crud.plate.update(
                self.session, db_obj=plate, obj_in=update_plate
            )
            if plate_update:
                logger.info(
                    f"new value plate.record_id ===> {plate_update.record_id}"
                )

    except Exception as exc:
        countdown = int(random.uniform(2, 4) ** self.request.retries)
        logger.info(f"Error adding record:{exc} ,retring in {countdown}s.")
        logger.exception(exc)
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):

    sender.add_periodic_task(
        settings.FREE_TIME_BETWEEN_RECORDS_ENTRANCEDOOR_EXITDOOR,
        set_status_record.s(),
        name="set status unknown for record after 24 hours becuse not exit",
    )

    logger.info(
        f"cleanup {settings.CLEANUP_COUNT} images every {settings.CLEANUP_PERIOD} seconds "
        f"which are older than {settings.CLEANUP_AGE} days"
    )
    if settings.CLEANUP_AGE > 0:
        sender.add_periodic_task(
            settings.CLEANUP_PERIOD,
            cleanup.s("image"),
            name="cleanup image task",
        )
        sender.add_periodic_task(
            settings.CLEANUP_PERIOD,
            cleanup.s("plate"),
            name="cleanup plate task",
        )
        sender.add_periodic_task(
            settings.CLEANUP_PERIOD,
            cleanup.s("record"),
            name="cleanup record task",
        )


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    acks_late=True,
    max_retries=1,
    soft_time_limit=240,
    time_limit=360,
    name="set_status_record",
)
def set_status_record(self):

    try:
        records = crud.record.get_multi_record(
            self.session,
            input_status_record=StatusRecord.unfinished.value,
            input_create_time=datetime.now()
            - timedelta(
                seconds=settings.FREE_TIME_BETWEEN_RECORDS_ENTRANCEDOOR_EXITDOOR
            ),
        )
        if records:
            for record in records:
                logger.info(
                    f"this plate {record.plate} after {timedelta(seconds=settings.FREE_TIME_BETWEEN_RECORDS_ENTRANCEDOOR_EXITDOOR)} hour not exieted"
                )
                record.latest_status = StatusRecord.unknown.value
                crud.record.update(self.session, db_obj=record)
    except:
        print("Not found")
        print("func set status")


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    acks_late=True,
    max_retries=1,
    soft_time_limit=240,
    time_limit=360,
    name="cleanup",
)
def cleanup(self, table_name: str = "image"):
    """cleans db up and wait at least CLEANUP_PERIOD seconds between each operation"""
    lock_name = f"cleanup_{table_name}_task_lock"
    if redis_client.get(lock_name):
        return f"Cleanup {table_name} canceled for performance"
    redis_client.setex(
        lock_name, timedelta(seconds=60 * settings.CLEANUP_PERIOD), 1
    )
    result = None
    try:
        if table_name == "image":
            model_img = models.Image
            img_ids = crud.image.get_multi(self.session)
            for img_id in img_ids:
                subquery = (
                    self.session.query(model_img.id)
                    .filter(
                        model_img.modified
                        < (
                            datetime.now(timezone.utc)
                            - timedelta(days=settings.CLEANUP_AGE)
                        ),
                        model_img.id != img_id.id,
                    )
                    .limit(settings.CLEANUP_COUNT)
                    .subquery()
                )
                result = (
                    self.session.query(model_img)
                    .filter(model_img.id.in_(subquery))
                    .delete(synchronize_session="fetch")
                )
        elif table_name == "plate":
            limit = datetime.now() - timedelta(
                days=settings.CLEANUP_PLATES_AGE
            )
            filter = models.Plate.record_time
            model = models.Plate
        elif table_name == "record":
            limit = datetime.now(timezone.utc) - timedelta(
                days=settings.CLEANUP_RECORDS_AGE
            )
            filter = models.Record.end_time
            model = models.Record
        else:
            return f"Cleanup Unknown Table ({table_name})!"
        logger.info(
            f"running cleanup {table_name} ({settings.CLEANUP_COUNT}, {settings.CLEANUP_AGE})"
        )
        if table_name != "image":
            subquery = (
                self.session.query(model.id)
                .filter(filter < limit)
                .limit(settings.CLEANUP_COUNT)
                .subquery()
            )
            result = (
                self.session.query(model)
                .filter(model.id.in_(subquery))
                .delete(synchronize_session="fetch")
            )
        self.session.commit()
        redis_client.setex(
            lock_name, timedelta(seconds=settings.CLEANUP_PERIOD), 1
        )
        return f"Cleanup {table_name} done, result: {result}"
    finally:
        redis_client.setex(
            lock_name, timedelta(seconds=settings.CLEANUP_PERIOD), 1
        )
