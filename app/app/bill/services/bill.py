from datetime import datetime, timedelta
from app.pricing.repo import price_repo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.db.base_class import get_now_datetime_utc
from app.bill.schemas import bill as billSchemas
from app.bill.repo import bill_repo, payment_bill_repo
from app.payment.repo import payment_repo
from app.payment.schemas import payment as paymentSchemas
from app.core.exceptions import ServiceFailure
from app.utils import MessageCodes
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

    # TODO FIX
    ...
    # zone_price, model_price = await zoneprice_repo.get_price_zone_async(
    #     db, zone_id=zone_id
    # )

    # if not model_price:
    #     raise ServiceFailure(
    #         detail="not set model price for this zone",
    #         msg_code=MessageCodes.not_found,
    #     )

    # duration_time = convert_time_to_hour_and_ceil(start_time_in, end_time_in)
    # price = model_price.entrance_fee + (duration_time * model_price.hourly_fee)
    # return price


def calculate_price(
    db: Session,
    *,
    zone_id: int,
    start_time_in: datetime,
    end_time_in: datetime,
) -> float:
    # TODO FIX
    ...
    # zone_price, model_price = zoneprice_repo.get_price_zone(
    #     db, zone_id=zone_id
    # )

    # if not model_price:
    #     raise ServiceFailure(
    #         detail="not set model price for this zone",
    #         msg_code=MessageCodes.not_found,
    #     )

    # duration_time = convert_time_to_hour_and_ceil(start_time_in, end_time_in)

    # price = model_price.entrance_fee + (duration_time * model_price.hourly_fee)

    # return price


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
        payment = await payment_repo.create(
            db, obj_in=paymentSchemas.PaymentCreate(price=bill.price)
        )

        await payment_bill_repo.create(
            db,
            obj_in=billSchemas.PaymentBillCreate(
                bill_id=bill.id, payment_id=payment.id
            ),
        )

        # TODO send to payment gateway and call back update this
    return bill
