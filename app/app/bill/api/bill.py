from fastapi import APIRouter, Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from cache.redis import redis_connect_async
from datetime import datetime
from app import models
from app.api import deps
from app.core import exceptions as exc
from app.utils import (
    APIResponse,
    APIResponseType,
    PaginatedContent,
    MessageCodes,
)
from app.bill import services, schemas
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated, Any
from app.plate.repo import plate_repo
from app.plate.schemas import PlateType
import logging
from fastapi.responses import StreamingResponse

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
    params: schemas.ParamsBill = Depends(),
    jalali_date: schemas.JalaliDate = Depends(),
) -> APIResponseType[PaginatedContent[list[schemas.Bill]]]:
    """
    All bill.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    bills, count = await services.get_multi_by_filters(
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
) -> APIResponseType[schemas.Bill]:
    """
    get bill.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    bill, count = await services.get_multi_by_filters(
        db, params=schemas.ParamsBill(input_id=id)
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
    bills_paid, bills_unpaid = await services.get_paid_unpaid_bills(
        db, plate=plate_in
    )

    return APIResponse(
        schemas.billsPaidUnpaidplate(
            paid=bills_paid,
            unpaid=bills_unpaid,
            user_info=schemas.PlateInfo(**plates_phone_number.__dict__),
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

    bills_paid, bills_unpaid = await services.get_bills_paid_unpaid(
        db, plate=plate_in, start_time=start_time, end_time=end_time
    )

    return APIResponse(
        schemas.billsPaidUnpaidplate(
            paid=bills_paid,
            unpaid=bills_unpaid,
            user_info=schemas.PlateInfo(**plates_phone_number.__dict__),
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

    bills_paid, bills_unpaid = await services.get_paid_unpaid_bills(
        db, plate=plate_in
    )

    return APIResponse(bills_unpaid)


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
    current_user: models.User = Depends(deps.get_current_active_user),
    bills_update: list[schemas.BillUpdate],
) -> APIResponseType[Any]:
    """
    create bill.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    result, msg_code = await services.update_multi_bill(
        db, bills_update=bills_update,current_user=current_user.id
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
    bill_in: schemas.BillCreate,
) -> APIResponseType[Any]:
    """
    create bill.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    bill = await services.create(db, bill_in=bill_in)

    return APIResponse(bill)


@router.post("/excel-police/")
async def download_excel(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    *,
    params: schemas.ParamsBill = Depends(),
    send_by: schemas.NoticeProvider = schemas.NoticeProvider.police,
    reg_notice: bool = False,
    input_excel_name: str = f"{datetime.now().date()}",
) -> StreamingResponse:
    """
    excel plate.
    user access to this [ ADMINISTRATOR ]
    """
    return await services.gen_excel_for_police(
        db,
        params=params,
        send_by=send_by,
        reg_notice=reg_notice,
        input_excel_name=input_excel_name,
    )


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
