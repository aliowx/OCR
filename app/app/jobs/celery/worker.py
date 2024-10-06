import logging
import math
import random
from datetime import datetime, timedelta, UTC
from sqlalchemy import text

from app import crud, models, schemas
from app.core.celery_app import DatabaseTask, celery_app
from app.core.config import settings
from app.jobs.celery.celeryworker_pre_start import redis_client
from app.schemas import EventUpdate, RecordUpdate, TypeEvent, StatusRecord

from app.bill.services.bill import calculate_price
from app.bill.repo import bill_repo
from app.bill.schemas import bill as billSchemas

from app.db.init_data_fake import create_events


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
    name="add_events",
)
def add_events(self, event: dict) -> str:

    try:
        event = crud.event.create(db=self.session, obj_in=event)

        celery_app.send_task(
            "update_record",
            args=[event.id],
        )

    except Exception as exc:
        countdown = int(random.uniform(1, 2) ** self.request.retries)
        logger.info(f"Error adding event:{exc} ,retrying in {countdown}s.")
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
def update_record(self, event_id) -> str:
    logger.info(f"******** update_record: {event_id}")

    if event_id == {}:
        logger.warning(f"Invalid event id found: {event_id}")
        return None

    if isinstance(event_id, dict) and "id" in event_id:
        event_id = event_id["id"]

    try:
        # lock events table to prevent multiple record insertion
        self.session.execute(text("LOCK TABLE event IN EXCLUSIVE MODE"))
        event = crud.event.get(self.session, event_id)
        record = crud.record.get_by_event(
            db=self.session,
            plate=event,
            status=StatusRecord.unfinished.value,
            for_update=True,
        )
        if (
            record is None
            and event.type_event != TypeEvent.exitDoor.value
            and event.type_event != TypeEvent.admin_exitRegistration.value
            and event.type_event
            != TypeEvent.admin_exitRegistration_and_billIssuance.value
        ):
            record = schemas.RecordCreate(
                plate=event.plate,
                start_time=event.record_time,
                end_time=event.record_time,
                score=0.01,
                img_entrance_id=event.lpr_image_id,
                img_exit_id=event.plate_image_id,
                spot_id=event.spot_id,
                zone_id=event.zone_id,
                latest_status=StatusRecord.unfinished.value,
            )
            record = crud.record.create(db=self.session, obj_in=record)
        elif record:
            record_update = None
            latest_status = StatusRecord.unfinished.value
            if (
                event.type_event == TypeEvent.exitDoor.value
                or event.type_event
                == TypeEvent.admin_exitRegistration_and_billIssuance.value
                or event.type_event == TypeEvent.admin_exitRegistration.value
            ):
                latest_status = StatusRecord.finished.value
            if record.start_time > event.record_time:
                record_update = RecordUpdate(
                    score=math.sqrt(record.score),
                    start_time=event.record_time,
                    latest_status=latest_status,
                )
            if record.end_time < event.record_time:
                record_update = RecordUpdate(
                    score=math.sqrt(record.score),
                    end_time=event.record_time,
                    img_entrance_id=event.lpr_image_id,
                    img_plate_exit_id=event.plate_image_id,
                    latest_status=latest_status,
                )
            if record_update is None:
                record_update = RecordUpdate(
                    score=math.sqrt(record.score),
                    latest_status=latest_status,
                )

            record = crud.record.update(
                self.session, db_obj=record, obj_in=record_update
            )

            if (
                record.latest_status == StatusRecord.finished
                and event.type_event != TypeEvent.admin_exitRegistration.value
            ):
                issued_by = billSchemas.Issued.exit_camera.value
                if (
                    event.type_event
                    == TypeEvent.admin_exitRegistration_and_billIssuance.value
                ):
                    issued_by = billSchemas.Issued.admin.value
                price, get_price = calculate_price(
                    self.session,
                    zone_id=record.zone_id,
                    start_time_in=record.start_time,
                    end_time_in=record.end_time,
                )
                bill = bill_repo.create(
                    self.session,
                    obj_in=billSchemas.BillCreate(
                        plate=record.plate,
                        start_time=record.start_time,
                        end_time=record.end_time,
                        issued_by=issued_by,
                        price=price,
                        record_id=record.id,
                        zone_id=record.zone_id,
                        status=billSchemas.StatusBill.unpaid.value,
                        entrance_fee=get_price.entrance_fee,
                        hourly_fee=get_price.hourly_fee,
                    ),
                )
                logger.info(f"issue bill {record} by number {bill}")

            update_event = EventUpdate(record_id=record.id)
            # this refresh for update event with out this not working ==> solution 1
            self.session.refresh(event)
            # or solution 2
            # logger.info(f"latest value event.record_id ===> {event.record_id}")
            # or solution 3
            # event.record_id = record.id
            # event_update = crud.event.update(
            #     self.session, db_obj=event
            # )

            event_update = crud.event.update(
                self.session, db_obj=event, obj_in=update_event
            )
            if event_update:
                logger.info(
                    f"new value event.record_id ===> {event_update.record_id}"
                )

    except Exception as exc:
        countdown = int(random.uniform(2, 4) ** self.request.retries)
        logger.info(f"Error adding record:{exc} ,retring in {countdown}s.")
        logger.exception(exc)
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):

    sender.add_periodic_task(
        settings.AUTO_GEN_EVENT_FAKE,
        set_status_record.s(),
        name="set status unknown for record after 24 hours becuse not exit",
    )
    if settings.DATA_FAKE_SET:
        sender.add_periodic_task(
            settings.AUTO_GEN_EVENT_FAKE,
            set_fake_data.s(),
            name=f"set fake data every {settings.AUTO_GEN_EVENT_FAKE}",
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
            cleanup.s("event"),
            name="cleanup event task",
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
            input_create_time=datetime.now(UTC).replace(tzinfo=None)
            - timedelta(
                seconds=settings.FREE_TIME_BETWEEN_RECORDS_ENTRANCEDOOR_EXITDOOR
            ),
        )
        if records:
            for record in records:
                logger.info(
                    f"this event {record.plate} after {timedelta(seconds=settings.FREE_TIME_BETWEEN_RECORDS_ENTRANCEDOOR_EXITDOOR)} hour not exieted"
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
    name="gen_fake_data",
)
def set_fake_data(self):

    try:
        create_events(self.session)
    except Exception as e:
        print(f"error set data fake {e}")


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
                            datetime.now(UTC).replace(tzinfo=None)
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
        elif table_name == "event":
            limit = datetime.now(UTC).replace(tzinfo=None) - timedelta(
                days=settings.CLEANUP_EVENTS_AGE
            )
            filter = models.Event.record_time
            model = models.Event
        elif table_name == "record":
            limit = datetime.now(UTC).replace(tzinfo=None) - timedelta(
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
