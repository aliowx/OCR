import logging

from fastapi import APIRouter, Depends, Query, WebSocket
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from cache.redis import redis_connect_async
from datetime import datetime, UTC
from app import models
from app.api import deps
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType
from app.bill.repo import bill_repo
from app.utils import PaginatedContent, MessageCodes
from app.bill.schemas import bill as billSchemas
from app.bill.services import bill as servicesBill
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated, Any
import rapidjson
from cache.redis import redis_client
from app.plate.repo import plate_repo
from app.plate.schemas import PlateType

router = APIRouter()
namespace = "bill"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_bill(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    params: billSchemas.ParamsBill = Depends(),
    jalali_date: billSchemas.JalaliDate = Depends(),
) -> APIResponseType[PaginatedContent[list[billSchemas.Bill]]]:
    """
    All bill.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    bills, count = await servicesBill.get_multi_by_filters(
        db, params=params, jalali_date=jalali_date
    )
    return APIResponse(
        PaginatedContent(
            data=bills,
            total_count=count,
            page=params.page,
            size=params.size,
        )
    )


@router.get("/{id}")
async def get_bill(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                ]
            )
        ),
    ],
    id: int,
    db: AsyncSession = Depends(deps.get_db_async),
) -> APIResponseType[billSchemas.Bill]:
    """
    get bill.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    bill, count = await servicesBill.get_multi_by_filters(
        db, params=billSchemas.ParamsBill(input_id=id)
    )
    if not bill:
        raise exc.ServiceFailure(
            detail="bill not found",
            msg_code=MessageCodes.not_found,
        )
    return APIResponse(bill[0])


@router.get("/get-bills-by-plate-phone/")
async def get_bills_by_plate(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.APP_IRANMALL,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    plate_in: str,
    phone_number: str,
) -> APIResponseType[Any]:
    """
    Retrieve bills by plate and phone number.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , APP_IRANMALL ]
    """

    checking_phone_number = models.base.validate_iran_phone_number(
        phone_number
    )
    cheking_plate = models.base.validate_iran_plate(plate_in)

    plates_phone_number = await plate_repo.cheking_and_create_phone_number(
        db,
        phone_number=phone_number,
        plate=plate_in,
        type_list=PlateType.phone,
    )
    bills_paid, bills_unpaid = await servicesBill.get_paid_unpaid_bills(
        db, plate=plate_in
    )

    return APIResponse(
        billSchemas.billsPaidUnpaidplate(
            paid=bills_paid,
            unpaid=bills_unpaid,
            user_info=billSchemas.PlateInfo(**plates_phone_number.__dict__),
        )
    )


@router.get("/get-bills-by-plate/")
async def get_bills_by_plate(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.APP_IRANMALL,
                    UserRoles.APPS,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    plate_in: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> APIResponseType[Any]:
    """
    Retrieve bills by plate and phone number.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , APP_IRANMALL , APPS ]
    """

    cheking_plate = models.base.validate_iran_plate(plate_in)

    plates_phone_number = await plate_repo.exist_plate(
        db,
        plate=plate_in,
        type_list=PlateType.phone,
    )
    if plates_phone_number is None or plates_phone_number.phone_number is None:
        raise exc.ServiceFailure(
            detail="phone number not Found",
            msg_code=MessageCodes.not_found,
        )

    bills_paid, bills_unpaid = await servicesBill.get_bills_paid_unpaid(
        db, plate=plate_in, start_time=start_time, end_time=end_time
    )

    return APIResponse(
        billSchemas.billsPaidUnpaidplate(
            paid=bills_paid,
            unpaid=bills_unpaid,
            user_info=billSchemas.PlateInfo(**plates_phone_number.__dict__),
        )
    )


@router.get("/get-bills/")
async def get_bills_by_plate(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.ITOLL,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    plate_in: str,
) -> APIResponseType[Any]:
    """
    Retrieve bills by plate and phone number.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , ITOLL ]
    """

    cheking_plate = models.base.validate_iran_plate(plate_in)

    bills_paid, bills_unpaid = await servicesBill.get_paid_unpaid_bills(
        db, plate=plate_in
    )

    return APIResponse(bills_unpaid)


@router.get("/get_by_ids/")
async def get_by_ids(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    ids_in: Annotated[list[int], Query(...)],
) -> APIResponseType[list[billSchemas.BillNotAdditionalDetail] | Any]:
    """
    create bill.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    bills = []
    msg_code = 0
    for id in ids_in:
        bill = await bill_repo.get(db, id=id)
        if bill:
            bills.append(bill)
            if bill.rrn_number is not None:
                msg_code = 14
        if not bill:
            bills.append({"bill by this id not found": id})
    response = APIResponse(data=bills, msg_code=msg_code)
    return response


@router.put("/update_bills")
async def update_bills(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    bills_update: list[billSchemas.BillUpdate],
) -> APIResponseType[Any]:
    """
    create bill.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    result, msg_code = await servicesBill.update_multi_bill(
        db, bills_update=bills_update
    )

    return APIResponse(result, msg_code=msg_code)


@router.post("/create")
async def create_bill(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    bill_in: billSchemas.BillCreate,
) -> APIResponseType[Any]:
    """
    create bill.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    if bill_in.price is None:
        time_now = datetime.now(UTC).replace(tzinfo=None)
        price, get_price = await servicesBill.calculate_price_async(
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

    bill_ws.start_time = servicesBill.convert_to_timezone_iran(
        bill_ws.start_time
    )
    bill_ws.end_time = servicesBill.convert_to_timezone_iran(bill_ws.end_time)
    bill_ws.created = servicesBill.convert_to_timezone_iran(bill_ws.created)
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

    return APIResponse(bill)


@router.websocket("/bills")
async def websocket_endpoint(websocket: WebSocket, camera_id: int):
    await websocket.accept()
    connection = await redis_connect_async(240)  # 3 mins
    async with connection.pubsub() as channel:
        await channel.subscribe(f"bills:camera_{camera_id}")

        try:
            while True:
                data = await channel.get_message(
                    ignore_subscribe_messages=True, timeout=240
                )
                # data = await websocket.receive_text()
                if data and "data" in data:
                    print(data["data"])
                    await websocket.send_text(data["data"])
        except:
            channel.unsubscribe(f"bills:camera_{camera_id}")
