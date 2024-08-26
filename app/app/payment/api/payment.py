import logging
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from cache.redis import redis_connect_async

from app import crud, models, schemas, utils
from app.api import deps
from app.core import exceptions as exc
from app.core.celery_app import celery_app
from app.utils import APIResponse, APIResponseType
from app.payment.repo import payment_repo
from app.bill.repo import bill_repo, payment_bill_repo
from app.utils import PaginatedContent, MessageCodes
from app.payment.schemas import payment as paymentSchemas

from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated


router = APIRouter()
namespace = "payment"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_payment(
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
    params: paymentSchemas.ParamsPayment = Depends(),
) -> APIResponseType[PaginatedContent[list[paymentSchemas.Payment]]]:
    """
    All payments.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    payments = await payment_repo.get_multi_by_filters(db, params=params)
    return APIResponse(
        PaginatedContent(
            data=payments[0],
            total_count=payments[1],
            page=params.page,
            size=params.size,
        )
    )


@router.post("/")
async def payment(
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
    ids_bill: list[int],
    pay: bool = False,
) -> APIResponseType[paymentSchemas.CreatePaymentByBill]:
    """
    bulk payment or one payment.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    bills = await bill_repo.get_all_by_ids(db, ids=ids_bill)

    if not bills:
        raise exc.ServiceFailure(
            detail=f"bill not exist", msg_code=MessageCodes.not_found
        )

    total_price = 0

    total_price = sum(bill.price for bill in bills if bill.price)

    if pay:
        payment = await payment_repo.create(
            db, obj_in=paymentSchemas.PaymentCreate(price=total_price)
        )

        for bill in bills:
            await payment_bill_repo.create(
                db,
                obj_in=paymentSchemas.PaymentBillCreate(
                    bill_id=bill.id, payment_id=payment.id
                ),
            )

    return APIResponse(
        paymentSchemas.CreatePaymentByBill(
            total_price=total_price,
            payment=payment if pay else None,
            bills=jsonable_encoder(bills),
        )
    )
