import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from cache.redis import redis_connect_async

from app import crud, models, schemas, utils
from app.api import deps
from app.core import exceptions as exc
from app.core.celery_app import celery_app
from app.utils import APIResponse, APIResponseType
from app.payment.repo import payment_repo
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


