import logging

from fastapi import APIRouter, Depends, Query, WebSocket
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from cache.redis import redis_connect_async
from datetime import datetime, UTC
from app import crud, schemas
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

    bills = await bill_repo.get_multi_by_filters(
        db, params=params, jalali_date=jalali_date
    )
    for bill in bills[0]:
        await servicesBill.set_detail(db, bill=bill)
    return APIResponse(
        PaginatedContent(
            data=bills[0],
            total_count=bills[1],
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
    bill = await bill_repo.get(db, id=id)
    if not bill:
        raise exc.ServiceFailure(
            detail="bill not found",
            msg_code=MessageCodes.not_found,
        )
    bill = await servicesBill.set_detail(db, bill=bill)
    return APIResponse(bill)


@router.post("/kiosk")
async def create_bill_by_kiosk(
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
    plate_in: str,
    issue: bool = None,
    db: AsyncSession = Depends(deps.get_db_async),
) -> APIResponseType[Any]:
    """
    create bill.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    record = await crud.record.get_record(
        db,
        input_plate=plate_in,
        input_status=schemas.StatusRecord.unfinished.value,
    )
    if record:
        record = await servicesBill.kiosk(db, record=record, issue=issue)
    else:
        record = await crud.record.get_record(
            db,
            input_plate=plate_in,
            input_status=schemas.StatusRecord.finished.value,
        )
    return APIResponse(record)


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
    redis_client.publish("bills:1", rapidjson.dumps(jsonable_encoder(bill)))

    return APIResponse(bill)


@router.websocket("/bills")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection = await redis_connect_async(240)  # 3 mins
    async with connection.pubsub() as channel:
        await channel.subscribe("bills:1")
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
            channel.unsubscribe("bills:1")
