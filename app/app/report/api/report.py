import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
from app import crud, models, schemas, utils
from app.api import deps
from app.core import exceptions as exc
from app.report import schemas as report_schemas
from app.report import services as report_services
from app.utils import APIResponse, APIResponseType, PaginatedContent
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated


router = APIRouter()
namespace = "report"
logger = logging.getLogger(__name__)


# @router.get("/status-parking-by-zone")
async def zone_status(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.REPORTING_ANALYSIS,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
    params: report_schemas.ReadZoneLotsParams = Depends(),
) -> APIResponseType[PaginatedContent[list[report_schemas.ZoneLots]]]:

    return APIResponse(await report_services.report_zone(db, params))


@router.get("/dashboard")
async def dashboard(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.REPORTING_ANALYSIS,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
    return APIResponse(await report_services.dashboard(db))


@router.get("/record-moment")
async def zone_status(
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:

    return APIResponse(await report_services.report_moment(db))
