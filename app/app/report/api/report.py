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



@router.get("/capacity")
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
    
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , REPORTING_ANALYSIS ]
    """

    return APIResponse(await report_services.capacity(db))


@router.get("/average_time")
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
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , REPORTING_ANALYSIS ]
    """

    return APIResponse(await report_services.average_time(db))


@router.get("/avrage_referrd")
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
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , REPORTING_ANALYSIS ]
    """

    return APIResponse(await report_services.avrage_referrd(db))


@router.get("/max_time_park")
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
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , REPORTING_ANALYSIS ]
    """

    return APIResponse(await report_services.max_time_park(db))


@router.get("/record-moment")
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
) -> APIResponseType[Any]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , REPORTING_ANALYSIS ]
    """

    return APIResponse(await report_services.report_moment(db))
