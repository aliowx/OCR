import logging
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base_class import get_now_datetime_utc
from cache.redis import redis_connect_async

from app import crud, models, schemas, utils
from app.api import deps
from app.core import exceptions as exc
from app.core.celery_app import celery_app
from app.utils import APIResponse, APIResponseType
from app.bill.repo import bill_repo
from app.utils import PaginatedContent, MessageCodes
from app.bill.schemas import bill as billSchemas
from datetime import datetime, timedelta
from app.bill.services.bill import calculate_price, convert_time_to_hour
from app.payment.repo import payment_repo
from app.payment.schemas import payment as paymentSchemas

from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated


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
    params: billSchemas.ParamsBill = Depends(),
) -> APIResponseType[PaginatedContent[list[billSchemas.Bill]]]:
    """
    All bill.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    bills = await bill_repo.get_multi_by_filters(db, params=params)
    
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
    issue: bool = False,
    db: AsyncSession = Depends(deps.get_db_async),
) -> APIResponseType[billSchemas.Bill | billSchemas.BillShowBykiosk]:
    """
    create bill.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    record = await crud.record.get_record(
        db,
        input_plate=plate_in,
        input_status=schemas.StatusRecord.unfinished.value,
    )
    if not record:
        raise exc.ServiceFailure(
            detail="plate not in parking",
            msg_code=MessageCodes.not_found,
        )
    end_time = get_now_datetime_utc()
    bill = billSchemas.BillShowBykiosk(
        plate=record.plate,
        start_time=record.start_time,
        end_time=end_time,
        issued_by=billSchemas.Issued.kiosk.value,
        price=calculate_price(
            start_time_in=record.start_time, end_time_in=end_time
        ),
        time_park_so_far=convert_time_to_hour(
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
                price=round(bill.price, 3),
            ).model_dump(),
        )
        payment = await payment_repo.create(
            db,
            obj_in=paymentSchemas.PaymentCreate(bill_id=bill.id).model_dump(),
        )
        # TODO send to payment gateway and call back update this

    return APIResponse(bill)
