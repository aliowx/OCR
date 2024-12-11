import logging
import math
import random
from datetime import datetime, timedelta, UTC
from sqlalchemy import text
from fastapi.encoders import jsonable_encoder
from app import crud, models, schemas
from app.bill import repo
from app.core.celery_app import DatabaseTask, celery_app
from app.core.config import settings
from app.jobs.celery.celeryworker_pre_start import redis_client
from app.schemas import TypeEvent, StatusRecord
import rapidjson
from app.models.base import EquipmentType, EquipmentStatus
from app.bill.services.bill import calculate_price, convert_to_timezone_iran
from app.bill.repo import bill_repo
from app.bill.schemas import bill as billSchemas
from app.parking.repo import equipment_repo
from app.db.init_data_fake import create_events
from app.notifications.repo import notifications_repo, equipment_repo
from app.notifications.schemas import NotificationsCreate, TypeNotice
from app.plate.schemas import PlateType
from app.plate.models import PlateList
import requests
import asyncio
import websockets 

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
        create_event = crud.event.create(db=self.session, obj_in=event)

        black_list = (
            self.session.query(PlateList)
            .filter(
                PlateList.plate == create_event.plate,
                PlateList.type == PlateType.black,
            )
            .first()
        )

        if black_list:
            notification = notifications_repo.create(
                self.session,
                obj_in=NotificationsCreate(
                    plate_list_id=black_list.id,
                    event_id=create_event.id,
                    type_notice=TypeNotice.black_list,
                    text=f"{black_list.plate}",
                ),
            )
            logger.info(
                f"found black listed plate {black_list.plate} in event id {create_event.id}, {notification}"
            )
            notice = jsonable_encoder(black_list)
            zone_name = (
                self.session.query(models.Zone.name)
                .filter(create_event.zone_id == models.Zone.id)
                .first()
            )
            notice["zone_name"] = zone_name[0] if zone_name else None

            camera_name = (
                self.session.query(models.Equipment.tag)
                .filter(create_event.camera_id == models.Equipment.id)
                .first()
            )
            notice["camera_name"] = camera_name[0] if camera_name else None
            redis_client.publish(
                "notifications",
                rapidjson.dumps(notice),
            )
        if create_event.invalid == False or (
            (
                create_event.invalid == True
                and create_event.type_event == TypeEvent.exitDoor
            )
            or (
                create_event.type_event
                == TypeEvent.approaching_leaving_unknown
            )
        ):
            celery_app.send_task(
                "update_record",
                args=[create_event.id],
            )

    except Exception as exc:
        countdown = int(random.uniform(1, 2) ** self.request.retries)
        logger.info(f"Error adding event:{exc} ,retrying in {countdown}s.")
        logger.exception(exc)
        raise self.retry(exc=exc, countdown=countdown)


def send_sms(phone, text: str):
    params_sending = {
        "phoneNumber": phone,
        "textMessage": text,
    }
    send_code = requests.post(
        settings.URL_SEND_SMS,
        params=params_sending,
    )


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    acks_late=True,
    max_retries=3,
    soft_time_limit=240,
    time_limit=360,
    name="update_record",
)
def update_record(
    self, event_id, combined_record_ids: list[int] | None = None
) -> str:

    logger.info(f"update_record: {event_id}")
    if event_id == {}:
        logger.warning(f"Invalid event id found: {event_id}")
        return None

    if isinstance(event_id, dict) and "id" in event_id:
        event_id = event_id["id"]

    try:
        # lock events table to prevent multiple record insertion
        self.session.execute(text("LOCK TABLE event IN EXCLUSIVE MODE"))
        event = crud.event.get(self.session, event_id)
        payment_type = crud.parking_repo.get_main_parking_sync(db=self.session)
        get_type_camera = crud.equipment_repo.get(
            self.session, id=event.camera_id
        ).equipment_type

        if event.type_event in (
            TypeEvent.exitDoor.value,
            TypeEvent.entranceDoor.value,
            TypeEvent.admin_exitRegistration_and_billIssuance.value,
            TypeEvent.admin_exitRegistration.value,
        ):
            direction = (
                "exit"
                if event.type_event
                in (
                    TypeEvent.exitDoor.value,
                    TypeEvent.admin_exitRegistration_and_billIssuance.value,
                    TypeEvent.admin_exitRegistration.value,
                )
                else "entry"
            )
        elif event.type_event == TypeEvent.approaching_leaving_unknown:
            direction = event.direction_info.get("direction")
            if direction is not None:
                if direction < 0:
                    direction = (
                        "exit"
                        if get_type_camera
                        == EquipmentType.CAMERA_DIRECTION_EXIT.value
                        else "entry"
                    )
                else:
                    direction = (
                        "entry"
                        if get_type_camera
                        == EquipmentType.CAMERA_DIRECTION_EXIT.value
                        else "exit"
                    )
            else:
                direction = "unknown"
        else:  # sensors, etc...
            direction = "sensor"

        record = crud.record.get_by_event(
            db=self.session,
            plate=event,
            status=StatusRecord.unfinished.value,
            for_update=True,
        )
        if event.type_event in (
            TypeEvent.admin_exitRegistration_and_billIssuance.value,
            TypeEvent.admin_exitRegistration.value,
        ):
            record = crud.record.get_by_event_by_admin(
                db=self.session,
                plate=event,
                status=[
                    StatusRecord.unfinished.value,
                    StatusRecord.unknown.value,
                ],
                for_update=True,
            )

        is_white_listed = (
            self.session.query(PlateList)
            .filter(
                PlateList.plate == event.plate,
                PlateList.type == PlateType.white,
            )
            .first()
        )

        is_phone_listed = (
            self.session.query(PlateList)
            .filter(
                PlateList.plate == event.plate,
                PlateList.type == PlateType.phone,
            )
            .first()
        )

        logger.info(
            f"update_record: {event_id}, {record}, {direction}, {get_type_camera}, {event.camera_id}"
        )

        if record is None:
            if event.invalid:
                return None

            # set_latest_status = StatusRecord.unfinished.value
            # img_entrance_id = event.lpr_image_id
            # img_plate_entrance_id = event.plate_image_id
            # img_exit_id = None
            # img_plate_exit_id = None

            if direction in ("exit", "unknown"):
                # check last minutes for any finished record
                finished_record = crud.record.get_by_event_by_admin(
                    db=self.session,
                    plate=event,
                    status=[
                        StatusRecord.finished.value,
                    ],
                    for_update=True,
                )
                if (
                    finished_record
                    and abs(event.record_time - finished_record.end_time)
                    < timedelta(minutes=5)
                    and finished_record.camera_exit_id == event.camera_id
                ):
                    print(f"extend {event} {finished_record}")

                    finished_record.end_time = max(
                        finished_record.end_time, event.record_time
                    )

                    finished_record.img_exit_id = event.lpr_image_id
                    finished_record.img_plate_exit_id = event.plate_image_id

                    finished_record = crud.record.update(
                        self.session, db_obj=finished_record
                    )

                    # update event relation to record
                    event.record_id = finished_record.id
                    event = crud.event.update(db=self.session, db_obj=event)

                    return

            if direction in ("entry", "unknown", "sensor"):
                set_latest_status = StatusRecord.unfinished.value
                img_entrance_id = event.lpr_image_id
                img_plate_entrance_id = event.plate_image_id
                camera_entrance_id = event.camera_id
                img_exit_id = None
                img_plate_exit_id = None
                camera_exit_id = None
            elif direction == "exit":
                set_latest_status = StatusRecord.finished.value
                img_entrance_id = None
                img_plate_entrance_id = None
                camera_entrance_id = None
                img_exit_id = event.lpr_image_id
                img_plate_exit_id = event.plate_image_id
                camera_exit_id = event.camera_id

            record = schemas.RecordCreate(
                plate=event.plate,
                start_time=event.record_time,
                end_time=event.record_time,
                score=0.01,
                img_entrance_id=img_entrance_id,
                img_plate_entrance_id=img_plate_entrance_id,
                spot_id=event.spot_id,
                zone_id=event.zone_id,
                latest_status=set_latest_status,
                camera_entrance_id=camera_entrance_id,
                img_exit_id=img_exit_id,
                img_plate_exit_id=img_plate_exit_id,
                camera_exit_id=camera_exit_id,
            )
            record = crud.record.create(db=self.session, obj_in=record)

            # update event relation to record
            event.record_id = record.id
            event = crud.event.update(db=self.session, db_obj=event)

            if (
                payment_type.payment_type
                == models.base.ParkingPaymentType.BEFORE_ENTER.value
                and combined_record_ids is None
            ):
                price, get_price = calculate_price(
                    self.session,
                    zone_id=record.zone_id,
                    start_time_in=record.start_time,
                    end_time_in=record.end_time,
                )
                issued_by = billSchemas.Issued.entrance.value
                status = billSchemas.StatusBill.unpaid.value
                bill_type = billSchemas.BillType.system.value
                if is_white_listed is not None:
                    status = billSchemas.StatusBill.paid.value
                    bill_type = billSchemas.BillType.free.value
                    price = 0
                bill_data = billSchemas.BillCreate(
                    plate=record.plate,
                    start_time=record.start_time,
                    end_time=record.end_time,
                    issued_by=issued_by,
                    price=price,
                    record_id=record.id,
                    zone_id=record.zone_id,
                    status=status,
                    entrance_fee=get_price.entrance_fee,
                    hourly_fee=get_price.hourly_fee,
                    camera_entrance_id=record.camera_entrance_id,
                    bill_type=bill_type,
                    img_entrance_id=record.img_entrance_id,
                )

                if is_phone_listed:
                    bill_data.notice_sent_at = datetime.now(UTC).replace(
                        tzinfo=None
                    )
                    bill_data.notice_sent_by = (
                        billSchemas.NoticeProvider.iranmall
                    )
                bill = bill_repo.create(self.session, obj_in=bill_data)
                if bill is not None:
                    bill.start_time = convert_to_timezone_iran(bill.start_time)
                    bill.end_time = convert_to_timezone_iran(bill.end_time)
                    bill.created = convert_to_timezone_iran(bill.created)
                    redis_client.publish(
                        f"bills:camera_{bill.camera_entrance_id}",
                        rapidjson.dumps(jsonable_encoder(bill)),
                    )
                    if is_phone_listed:
                        # send_sms(
                        #     is_phone_listed.phone_number,
                        #     f"{settings.TEXT_BILL}{bill.id}",
                        # )
                        send_sms(
                            is_phone_listed.phone_number,
                            f"{settings.TEXT_BILL}",
                        )

        else:  # record is not None:
            if event.invalid and direction != "exit":
                return

            if direction in ("exit", "unknown"):
                if (
                    abs(event.record_time - record.start_time)
                    < timedelta(minutes=2)
                    and record.camera_entrance_id == event.camera_id
                ):
                    logger.info(f"ignored {record}")
                else:
                    record.camera_exit_id = event.camera_id
                    record.img_exit_id = event.lpr_image_id
                    record.img_plate_exit_id = event.plate_image_id
                    record.latest_status = StatusRecord.finished.value

            if direction in ("entry", "sensor"):
                record.latest_status = StatusRecord.unfinished.value

            record.score = math.sqrt(record.score)

            if record.start_time > event.record_time:
                record.start_time = event.record_time
                record.camera_entrance_id = event.camera_id
                record.img_entrance_id = event.lpr_image_id
                record.img_plate_entrance_id = event.plate_image_id

            elif record.end_time < event.record_time:
                record.end_time = event.record_time

                # TODO: we should save current status too
                # record.camera_current_id = event.camera_id
                # record.img_current_id = event.lpr_image_id
                # record.img_plate_current_id = event.plate_image_id

            # update event relation to record
            event.record_id = record.id
            event = crud.event.update(db=self.session, db_obj=event)

            # merge multi record
            if (
                combined_record_ids is not None
                and len(combined_record_ids) > 1
            ):
                record.combined_record_ids = combined_record_ids

            record = crud.record.update(self.session, db_obj=record)

            if (
                record.latest_status == StatusRecord.finished
                and event.type_event != TypeEvent.admin_exitRegistration.value
                and payment_type.payment_type
                != models.base.ParkingPaymentType.BEFORE_ENTER.value
                and combined_record_ids is None
            ):
                price, get_price = calculate_price(
                    self.session,
                    zone_id=record.zone_id,
                    start_time_in=record.start_time,
                    end_time_in=record.end_time,
                )
                issued_by = billSchemas.Issued.exit_camera.value
                status = billSchemas.StatusBill.unpaid.value
                bill_type = billSchemas.BillType.system.value
                if (
                    event.type_event
                    == TypeEvent.admin_exitRegistration_and_billIssuance.value
                ):
                    issued_by = billSchemas.Issued.admin.value
                if is_white_listed:
                    status = billSchemas.StatusBill.paid.value
                    bill_type = billSchemas.BillType.free.value
                    price = 0
                bill_data = billSchemas.BillCreate(
                    plate=record.plate,
                    start_time=record.start_time,
                    end_time=record.end_time,
                    issued_by=issued_by,
                    price=price,
                    record_id=record.id,
                    zone_id=record.zone_id,
                    status=status,
                    entrance_fee=get_price.entrance_fee,
                    hourly_fee=get_price.hourly_fee,
                    camera_entrance_id=record.camera_entrance_id,
                    camera_exit_id=record.camera_exit_id,
                    bill_type=bill_type,
                )
                if is_phone_listed:
                    bill_data.notice_sent_at = datetime.now(UTC).replace(
                        tzinfo=None
                    )
                    bill_data.notice_sent_by = (
                        billSchemas.NoticeProvider.iranmall
                    )

                bill = bill_repo.create(self.session, obj_in=bill_data)
                if bill is not None:
                    bill.start_time = convert_to_timezone_iran(bill.start_time)
                    bill.end_time = convert_to_timezone_iran(bill.end_time)
                    bill.created = convert_to_timezone_iran(bill.created)
                    redis_client.publish(
                        f"bills:camera_{bill.camera_entrance_id}",
                        rapidjson.dumps(jsonable_encoder(bill)),
                    )
                    if is_phone_listed:
                        # send_sms(
                        #     is_phone_listed.phone_number,
                        #     f"{settings.TEXT_BILL}{bill.id}",
                        # )
                        send_sms(
                            is_phone_listed.phone_number,
                            f"{settings.TEXT_BILL}",
                        )
                logger.info(f"issue bill {record} by number {bill}")

    except Exception as exc:
        countdown = int(random.uniform(2, 4) ** self.request.retries)
        logger.info(f"Error adding record:{exc} ,retring in {countdown}s.")
        logger.exception(exc)
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    if settings.TIME_SEND_SMS_HEALTH_CHECK_EQUIPMENT > 0:
        sender.add_periodic_task(
            settings.TIME_SEND_SMS_HEALTH_CHECK_EQUIPMENT,
            health_check_equipment.s(),
            name=f"equipment is broken or disconnect",
        )
    sender.add_periodic_task(
        settings.CHECKING_FREE_TIME_BETWEEN_RECORDS_ENTRANCEDOOR_EXITDOOR,
        set_status_record.s(),
        name=f"set status unknown for record after {settings.FREE_TIME_BETWEEN_RECORDS_ENTRANCEDOOR_EXITDOOR} hours becuse not exit",
    )
    sender.add_periodic_task(
        10.0,
        check_health_ping_equipment.s(),
        name=f'set the helch chech statsu about the equipment '
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
    name="health_check_equipment",
)
def health_check_equipment(self):

    try:
        get_multi_equipment = equipment_repo.get_multi_active(self.session)
        for eq in get_multi_equipment:
            if eq.equipment_status in (
                EquipmentStatus.BROKEN,
                EquipmentStatus.DISCONNECTED,
            ):
                status = eq.equipment_status
                match status:
                    case models.base.EquipmentStatus.DISCONNECTED:
                        status = "قطع"
                    case models.base.EquipmentStatus.BROKEN:
                        status = "خراب"

                notification = notifications_repo.create(
                    self.session,
                    obj_in=NotificationsCreate(
                        text=f"دوربین {eq.tag} {status} است",
                        type_notice=TypeNotice.equipment,
                    ),
                )
                redis_client.publish(
                    "notifications",
                    rapidjson.dumps(f"دوربین {eq.tag} {status} است"),
                )

                for phone in settings.PHONE_LIST_REPORT_HEALTH_CHECK_EQUIPMENT:
                    send_sms(phone, f"دوربین {eq.tag} {status} است")
    except:
        print("no broken or disconnect")


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

@celery_app.task(
    base=DatabaseTask,
    bind=True,
    acks_late=True,
    max_retries=1,
    soft_time_limit=240,
    time_limit=360,
    name="checking health equipment",
)
def check_health_ping_equipment(self):
    try:
        get_multi_equipment = repo.equipment_repo.get_multi_active(
            self.session
        )
        for eq in get_multi_equipment:
            response = requests.get(
                f"https://dr-pms.iranmall.com/check/{eq.id}"
            )
            ping = response.json()["ping"]
            if eq.ping:
                if eq.ping > ping:
                    (eq.equipment_status == models.base.EquipmentStatus.HEALTHY.value)

                    eq.equipment_status = (
                        models.base.EquipmentStatus.HEALTHY.value)
                        
                    equipment = repo.equipment_repo.update(
                        self.session,
                        db_obj=eq,
                    )
                if eq.ping < ping:
                    check_time = redis_client.get(eq.tag)
                    if not check_time:
                        repo.notifications_repo.create(
                            self.session,
                            obj_in=schemas.notification.NotificationsCreate(
                                text=f"دوربین {eq.tag}  دچار خطا است",
                                type_notice=schemas.notification.TypeNotice.equipment,
                            ),
                        )
                    redis_client.set(
                        check_time,
                        check_time,
                        ex=settings.TIME_SEND_NOTICE_HEALTH_CHECK_EQUIPMENT,
                    )
                    redis_client.publish(
                        "notifications",
                        rapidjson.dumps(f"دوربین {eq.tag}  دچار خطا است"),
                    )
                    for phone in settings.PHONE_LIST_REPORT_HEALTH_CHECK_EQUIPMENT:
                        get_phone = redis_client.get(phone)
                        if not get_phone:
                            send_sms(
                                phone=phone,
                                text=f"دوربین {eq.tag}  دچار خطا است",
                            )
                            redis_client.set(
                                phone,
                                phone,
                                ex=settings.TIME_SEND_NOTICE_HEALTH_CHECK_EQUIPMENT,
                            )
    except Exception as e:
        logger.error(e)
