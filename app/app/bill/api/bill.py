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
from app.bill.repo import bill_repo
from app.utils import PaginatedContent
from app.bill.schemas import bill as billSchemas


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
    All plates.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    bills = await bill_repo.get_multi_by_filters(db, params=params)
    print(dir(bills))
    print(bills[0])
    print(bills[1])
    return APIResponse(
        PaginatedContent(
            data=bills[0],
            total_count=bills[1],
            page=params.page,
            size=params.size,
        )
    )
