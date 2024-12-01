from datetime import datetime, UTC
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.bill.schemas import bill as billSchemas
from app.bill.repo import bill_repo
from app.core.exceptions import ServiceFailure
from app.utils import MessageCodes, generate_excel
from app.parking.repo import zone_repo
from cache.redis import redis_client
from app.plate.repo import plate_repo
from app.models.base import plate_alphabet_reverse
from app.core.config import settings
from app.users.repo import user
from app.payment.repo import transaction_repo
import rapidjson
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


async def create(
    db: AsyncSession,
    *,
    bill_in: billSchemas.BillCreate,
):
    if bill_in.price is None:
        time_now = datetime.now(UTC).replace(tzinfo=None)
        price, get_price = await calculate_price_async(
            db,
            start_time_in=time_now,
            end_time_in=time_now,
            zone_id=bill_in.zone_id,
        )
        bill_in.price = price
        bill_in.entrance_fee = get_price.entrance_fee
        bill_in.entrance_fee = get_price.hourly_fee
    bill = await bill_repo.create(db, obj_in=bill_in.model_dump())
    bill_ws = bill

    bill_ws.start_time = convert_to_timezone_iran(bill_ws.start_time)
    bill_ws.end_time = convert_to_timezone_iran(bill_ws.end_time)
    bill_ws.created = convert_to_timezone_iran(bill_ws.created)
    if bill_ws.camera_entrance_id:
        redis_client.publish(
            f"bills:camera_{bill_ws.camera_entrance_id}",
            rapidjson.dumps(jsonable_encoder(bill_ws)),
        )
    if bill_ws.camera_exit_id:
        redis_client.publish(
            f"bills:camera_{bill_ws.camera_exit_id}",
            rapidjson.dumps(jsonable_encoder(bill_ws)),
        )
    return bill


async def get_multi_by_filters(
    db: AsyncSession,
    params: billSchemas.ParamsBill,
    jalali_date: billSchemas.JalaliDate | None = None,
):

    bills = await bill_repo.get_multi_by_filters(
        db, params=params, jalali_date=jalali_date
    )

    # bills
    #       bills -> bills[0]
    #             bill -> bill[0]
    #             time_park -> bill[1]
    #             zone_name -> bill[2]
    #             camera_entrance -> bill[3]
    #             camera_exit -> bill[4]
    #             user_name -> bill[5]
    #             record -> bill[6]
    #       count -> bills[1]

    resualt = []
    for bill in bills[0]:
        bill[0].time_park = round(bill[1].total_seconds() / 60)
        bill[0].zone_name = bill[2]
        bill[0].camera_entrance = bill[3]
        bill[0].camera_exit = bill[4]
        bill[0].user_name = bill[5]
        bill[0].record = bill[6]
        resualt.append(bill[0])

    return resualt, bills[1]


async def get_paid_unpaid_bills(db: AsyncSession, *, plate: str):
    bills_unpaid = (
        await get_multi_by_filters(
            db,
            params=billSchemas.ParamsBill(
                input_plate=plate,
                input_status=billSchemas.StatusBill.unpaid.value,
            ),
        )
    )[0]
    bills_unpaid = [
        billSchemas.BillB2B(
            id=unpaid.id,
            plate=unpaid.plate,
            price=unpaid.price,
            status=unpaid.status,
            entry_time=unpaid.record.start_time,
            leave_time=unpaid.record.end_time,
        )
        for unpaid in bills_unpaid
    ]
    bills_paid = (
        await get_multi_by_filters(
            db,
            params=billSchemas.ParamsBill(
                input_plate=plate,
                input_status=billSchemas.StatusBill.paid.value,
            ),
        )
    )[0]
    bills_paid = [
        billSchemas.BillB2B(
            id=paid.id,
            plate=paid.plate,
            price=paid.price,
            status=paid.status,
            entry_time=paid.record.start_time,
            leave_time=paid.record.end_time,
        )
        for paid in bills_paid
    ]
    return bills_paid, bills_unpaid


async def checking_status_bill(db: AsyncSession, *, bill_id: int):
    bill = (
        await get_multi_by_filters(
            db, params=billSchemas.ParamsBill(input_id=bill_id)
        )
    )[0][0]

    if not bill:
        raise ServiceFailure(
            detail="bills not found",
            msg_code=MessageCodes.not_found,
        )
    get_user = await user.get_by_username(db, username=billSchemas.B2B.itoll)
    user_id = None
    if get_user is not None:
        user_id = get_user.id
    if bill.user_paid_id == user_id:
        if bill.status == billSchemas.StatusBill.unpaid:
            return billSchemas.BillShwoItoll(
                plate=bill.plate,
                price=bill.price,
                status=bill.status,
                entry_time=bill.record.start_time,
                leave_time=bill.record.end_time,
            )
        if (
            bill.status == billSchemas.StatusBill.paid
            and bill.rrn_number is not None
        ):
            order_id = None
            get_order_id = await transaction_repo.get_transaction_by_rrn(
                db, rrn=bill.rrn_number
            )
            if get_order_id:
                order_id = f"{get_order_id.transaction_number[:10]}{get_order_id.id}{get_order_id.transaction_number[10:]}"
            return billSchemas.BillShwoItoll(
                plate=bill.plate,
                price=bill.price,
                time_paid=bill.time_paid,
                status=bill.status,
                rrn_number=bill.rrn_number,
                entry_time=bill.record.start_time,
                leave_time=bill.record.end_time,
                paid_by=get_user.username,
                order_id=order_id,
            )
    paid_by = None
    if bill.status == billSchemas.StatusBill.paid:
        paid_by = "other"
    return billSchemas.BillShwoItoll(
        plate=bill.plate,
        price=bill.price,
        status=bill.status,
        paid_by=paid_by,
        entry_time=bill.record.start_time,
        leave_time=bill.record.end_time,
    )


async def get_bills_paid_unpaid(
    db: AsyncSession,
    *,
    plate: str,
    start_time: datetime,
    end_time: datetime,
    order_by: billSchemas.OrderByBill,
    asc: bool,
):
    bill_unpaid = await get_multi_by_filters(
        db,
        params=billSchemas.ParamsBill(
            input_plate=plate,
            input_status=billSchemas.StatusBill.unpaid.value,
            input_start_time=start_time,
            input_end_time=end_time,
            input_order_by=order_by,
            asc=asc,
        ),
    )
    bills_paid = await get_multi_by_filters(
        db,
        params=billSchemas.ParamsBill(
            input_plate=plate,
            input_status=billSchemas.StatusBill.paid.value,
            input_start_time=start_time,
            input_end_time=end_time,
            input_order_by=order_by,
            asc=asc,
        ),
    )
    return bills_paid[0], bill_unpaid[0]


async def update_multi_bill(
    db: AsyncSession,
    bills_update: list[billSchemas.BillUpdate],
    current_user: int,
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
                bill_in.user_paid_id = current_user
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


async def update_bills_by_ids(
    db: AsyncSession,
    bill_ids_in: list[int],
    rrn_number_in: str,
    status_in: billSchemas.StatusBill,
    time_paid_in: datetime,
):
    resualt = {}

    list_bills_update = []
    list_bills_not_update = []
    msg_code = 0
    for bill_id in bill_ids_in:
        bill = await bill_repo.get(db, id=bill_id, for_update=True)
        if bill:
            if bill.rrn_number is not None:
                msg_code = 14
                list_bills_not_update.append(bill)
            if bill.rrn_number is None:
                bill.rrn_number = rrn_number_in
                bill.status = status_in
                bill.time_paid = time_paid_in
                bill_update = await bill_repo.update(
                    db,
                    db_obj=bill,
                )
                list_bills_update.append(bill_update)

        if not bill:
            list_bills_not_update.append(
                {"bill by this id not found": bill_id}
            )
    resualt.update({"list_bills_update": list_bills_update})
    if list_bills_not_update != []:
        resualt.update({"list_bills_not_update": list_bills_not_update})
    return resualt, msg_code


async def gen_excel_for_police(
    db: AsyncSession,
    *,
    params: billSchemas.ParamsBill,
    send_by: billSchemas.NoticeProvider,
    reg_notice: bool,
    input_excel_name: str = f"{datetime.now().date()}",
):
    bills = (
        await get_multi_by_filters(
            db,
            params=params,
        )
    )[0]

    # delete plates have phone number in system
    get_phone_list = await plate_repo.get_phone_list(db)
    bills_for_notice = []
    notice_sent_at_and_by = []
    text_bill = settings.TEXT_BILL

    for bill in bills:
        if bill.plate not in get_phone_list:
            bills_for_notice.append(bill)
    excel_record = []
    for bill in bills_for_notice:
        modified_plate = bill.plate
        for k, v in plate_alphabet_reverse.items():
            modified_plate = (
                modified_plate[:2]
                + modified_plate[2:4].replace(v, k)
                + modified_plate[4:]
            )
        excel_record.append(
            billSchemas.ExcelItemForPolice(
                seri=modified_plate[:2],
                hrf=modified_plate[2:3],
                serial=modified_plate[3:6],
                iran=modified_plate[6:8],
                text=f"{text_bill}/{bill.id}",
            )
        )
        if reg_notice:
            bill.notice_sent_at = datetime.now(UTC).replace(tzinfo=None)
            bill.notice_sent_by = send_by
            notice_sent_at_and_by.append(bill)
    if excel_record != []:
        set_notice = await bill_repo.update_multi(
            db, db_objs=notice_sent_at_and_by
        )
        file = generate_excel.get_excel_file_response(
            data=excel_record, title=input_excel_name
        )
        return file
    raise ServiceFailure(
        detail="bills not found",
        msg_code=MessageCodes.not_found,
    )
