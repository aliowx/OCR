from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.db.base_class import get_now_datetime_utc
from app.bill.schemas import bill as billSchemas
from app.schemas.record import StatusRecord
from app.bill.repo import bill_repo
from app.core.exceptions import ServiceFailure
from app.utils import MessageCodes
from app.parking.repo import zone_repo
import pytz
import math

def convert_to_timezone_iran(time: datetime):
    if isinstance(time, str):
        time = datetime.fromisoformat(time)
    # Define Iran Standard Time timezone
    iran_timezone = pytz.timezone("Asia/Tehran")
    # If value is naive (no timezone), localize it to UTC
    if time.tzinfo is None:
        # Localize the naive datetime to UTC
        utc_time = pytz.utc.localize(time)
    else:
        # If it's already timezone aware, convert to UTC
        utc_time = time.astimezone(pytz.utc)
    # Convert to Iran Standard Time
    return utc_time.astimezone(iran_timezone)


def convert_time_to_hour_and_ceil(start_time, end_time):
    if start_time > end_time:
        return 0

    time_diff = end_time - start_time

    convert_time_to_hours = time_diff.total_seconds() / 3600

    ciel_hours = math.ceil(convert_time_to_hours)

    return ciel_hours


async def calculate_price_async(
    db: AsyncSession,
    *,
    zone_id: int,
    start_time_in: datetime,
    end_time_in: datetime,
) -> float:

    get_price = await zone_repo.get_price_zone_async(db, zone_id=zone_id)
    if not get_price:
        raise ServiceFailure(
            detail="not set model price for this zone",
            msg_code=MessageCodes.not_found,
        )

    duration_time = convert_time_to_hour_and_ceil(start_time_in, end_time_in)
    price = get_price.entrance_fee + (duration_time * get_price.hourly_fee)

    return price, get_price


def calculate_price(
    db: Session,
    *,
    zone_id: int,
    start_time_in: datetime,
    end_time_in: datetime,
) -> float:

    get_price = zone_repo.get_price_zone(db, zone_id=zone_id)

    if not get_price:
        raise ServiceFailure(
            detail="not set model price for this zone",
            msg_code=MessageCodes.not_found,
        )

    duration_time = convert_time_to_hour_and_ceil(start_time_in, end_time_in)

    price = get_price.entrance_fee + (duration_time * get_price.hourly_fee)

    return price, get_price


async def set_detail(db: AsyncSession, bill: billSchemas.Bill):

    bill.time_park = round(
        (bill.end_time - bill.start_time).total_seconds() / 60
    )
    if bill.zone_id:
        zone = await zone_repo.get(db, id=bill.zone_id)
        bill.zone_name = zone.name

    if bill.img_entrance_id:
        bill.camera_entrance = await bill_repo.get_camera_by_image_id(
            db, img_id=bill.img_entrance_id
        )

    if bill.img_exit_id:
        bill.camera_exit = await bill_repo.get_camera_by_image_id(
            db, img_id=bill.img_exit_id
        )

    return bill


async def kiosk(db: AsyncSession, *, record, issue: bool = None):
    bill_unpaid = await bill_repo.get_bill_by_record_id(
        db,
        record_id=record.id,
        bill_status=billSchemas.StatusBill.unpaid.value,
    )
    bill_paid = await bill_repo.get_bill_by_record_id(
        db, record_id=record.id, bill_status=billSchemas.StatusBill.paid.value
    )
    if bill_unpaid:
        if (
            bill_unpaid.created + timedelta(minutes=15)
            > get_now_datetime_utc()
        ):
            return bill_unpaid
    end_time = get_now_datetime_utc()
    # TODO fix hard code
    if bill_paid:
        if (
            bill_paid.time_paid + timedelta(minutes=15)
            > get_now_datetime_utc()
        ):
            return (
                billSchemas.BillShowBykiosk(
                    plate=bill_paid.plate,
                    start_time=bill_paid.start_time,
                    end_time=bill_paid.end_time,
                    issued_by=bill_paid.issued_by,
                    price=bill_paid.price,
                    entrance_fee=bill_paid.entrance_fee,
                    hourly_fee=bill_paid.hourly_fee,
                    time_park_so_far=convert_time_to_hour_and_ceil(
                        bill_paid.start_time, bill_paid.end_time
                    ),
                    status=bill_paid.status,
                ),
            )
        if (
            bill_paid.time_paid + timedelta(minutes=15)
            < get_now_datetime_utc()
            and record.latest_status == StatusRecord.unfinished
        ):
            price, get_price = await calculate_price_async(
                db,
                start_time_in=bill_paid.end_time,
                end_time_in=get_now_datetime_utc(),
                zone_id=bill_paid.zone_id,
            )
            bill = billSchemas.BillShowBykiosk(
                plate=bill_paid.plate,
                start_time=bill_paid.start_time,
                end_time=bill_paid.end_time,
                issued_by=bill_paid.issued_by,
                price=bill_paid.price,
                entrance_fee=get_price.entrance_fee,
                hourly_fee=get_price.hourly_fee,
                time_park_so_far=convert_time_to_hour_and_ceil(
                    bill_paid.start_time, bill_paid.end_time
                ),
            )
            # isuue True create bill
            if issue:
                bill = await bill_repo.create(
                    db,
                    obj_in=billSchemas.BillCreate(
                        plate=bill.plate,
                        start_time=bill.end_time,
                        end_time=get_now_datetime_utc(),
                        issued_by=bill.issued_by,
                        price=bill.price,
                        record_id=record.id,
                    ).model_dump(),
                )
            return bill
    else:
        price, get_price = await calculate_price_async(
            db,
            start_time_in=record.start_time,
            end_time_in=end_time,
            zone_id=record.zone_id,
        )
        bill = billSchemas.BillShowBykiosk(
            plate=record.plate,
            start_time=record.start_time,
            end_time=end_time,
            issued_by=billSchemas.Issued.kiosk.value,
            price=price,
            entrance_fee=get_price.entrance_fee,
            hourly_fee=get_price.hourly_fee,
            time_park_so_far=convert_time_to_hour_and_ceil(
                record.start_time, end_time
            ),
        )
        # isuue True create bill
        if issue:
            bill = await bill_repo.create(
                db,
                obj_in=billSchemas.BillCreate(
                    plate=bill.plate,
                    start_time=bill.start_time,
                    end_time=bill.end_time,
                    issued_by=bill.issued_by,
                    price=bill.price,
                    record_id=record.id,
                ).model_dump(),
            )

        return bill


async def update_multi_bill(
    db: AsyncSession, bills_update: list[billSchemas.BillUpdate]
):
    resualt = {}

    list_bills_update = []
    list_bills_not_update = []
    msg_code = 0
    for bill_in in bills_update:
        bill = await bill_repo.get(db, id=bill_in.id, for_update=True)
        if bill:
            if bill.rrn_number is not None:
                msg_code = 14
                list_bills_not_update.append(bill)
            if bill.rrn_number is None:
                bill_update = await bill_repo.update(
                    db, db_obj=bill, obj_in=bill_in.model_dump()
                )
                await db.commit()
                list_bills_update.append(bill_update)

        if not bill:
            list_bills_not_update.append(
                {"bill by this id not found": bill_in.id}
            )
    resualt.update({"list_bills_update": list_bills_update})
    if list_bills_not_update != []:
        resualt.update({"list_bills_not_update": list_bills_not_update})
    return resualt, msg_code
