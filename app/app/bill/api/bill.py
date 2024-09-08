import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from cache.redis import redis_connect_async

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

    bill = await servicesBill.kiosk(db, record=record, issue=issue)

    return APIResponse(bill)
