from datetime import datetime
from app.pricing.repo import price_repo
from sqlalchemy.ext.asyncio import AsyncSession
from app.parking.repo import zoneprice_repo
from sqlalchemy.orm import Session
from app.db.base_class import get_now_datetime_utc
from app.bill.schemas import bill as billSchemas
from app.bill.repo import bill_repo, payment_bill_repo
from app.payment.repo import payment_repo
from app.payment.schemas import payment as paymentSchemas


def convert_time_to_hour(start_time, end_time):
    if start_time > end_time:
        return 0
    days = 0
    time_diffrence = end_time - start_time

    # seprating day from time
    if time_diffrence.days:
        days = time_diffrence.days * 24
        time_diffrence = str(time_diffrence).split(", ")[
            1
        ]  # example 1 day, 00:00:00 -> 00:00:00
    # Calculation hours, conversion minutes and seconds to hours
    hours, minutes, seconds = map(float, str(time_diffrence).split(":"))
    hours = hours if hours > 0 else 0
    minutes = minutes / 60 if minutes > 0 else 0
    seconds = seconds / 3600 if seconds > 0 else 0
    time_diffrence = hours + minutes + seconds + days
    return time_diffrence


async def calculate_price(
    db: Session | AsyncSession,
    zone_id: int,
    start_time_in: datetime,
    end_time_in: datetime,
) -> float:

    model_price = await zoneprice_repo.get_price_zone(db, zone_id=zone_id)
    duration_time = convert_time_to_hour(start_time_in, end_time_in)

    price = model_price.entrance_fee + (duration_time * model_price.hourly_fee)

    return round(price, 4)


async def kiosk(db: AsyncSession, *, record, issue: bool = False):
    end_time = get_now_datetime_utc()
    bill = billSchemas.BillShowBykiosk(
        plate=record.plate,
        start_time=record.start_time,
        end_time=end_time,
        issued_by=billSchemas.Issued.kiosk.value,
        price=await calculate_price(
            db,
            start_time_in=record.start_time,
            end_time_in=end_time,
            zone_id=record.zone_id,
        ),
        time_park_so_far=round(
            convert_time_to_hour(record.start_time, end_time)
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
                price=round(bill.price, 3),
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
