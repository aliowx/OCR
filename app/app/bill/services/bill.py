from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.db.base_class import get_now_datetime_utc
from app.bill.schemas import bill as billSchemas
from app.bill.repo import bill_repo
from app.core.exceptions import ServiceFailure
from app.utils import MessageCodes
from app.parking.repo import zone_repo
import math


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

    price = await zone_repo.get_price_zone_async(db, zone_id=zone_id)
    if not price:
        raise ServiceFailure(
            detail="not set model price for this zone",
            msg_code=MessageCodes.not_found,
        )

    duration_time = convert_time_to_hour_and_ceil(start_time_in, end_time_in)
    price = price.entrance_fee + (duration_time * price.hourly_fee)
    return price


def calculate_price(
    db: Session,
    *,
    zone_id: int,
    start_time_in: datetime,
    end_time_in: datetime,
) -> float:

    price = zone_repo.get_price_zone(db, zone_id=zone_id)

    if not price:
        raise ServiceFailure(
            detail="not set model price for this zone",
            msg_code=MessageCodes.not_found,
        )

    duration_time = convert_time_to_hour_and_ceil(start_time_in, end_time_in)

    price = price.entrance_fee + (duration_time * price.hourly_fee)

    return price


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


async def kiosk(db: AsyncSession, *, record, issue: bool = False):
    end_time = get_now_datetime_utc()
    bill = billSchemas.BillShowBykiosk(
        plate=record.plate,
        start_time=record.start_time,
        end_time=end_time,
        issued_by=billSchemas.Issued.kiosk.value,
        price=await calculate_price_async(
            db,
            start_time_in=record.start_time,
            end_time_in=end_time,
            zone_id=record.zone_id,
        ),
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
