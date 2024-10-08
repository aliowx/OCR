import logging

from fastapi import APIRouter, Depends, Query
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
from typing import Annotated, Any


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
    
    bills = await bill_repo.get_multi_by_filters(db, params=params,jalali_date=jalali_date)
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

    return APIResponse(resualt, msg_code=msg_code)
