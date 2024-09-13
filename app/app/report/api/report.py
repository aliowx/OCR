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
from datetime import datetime

router = APIRouter()
namespace = "report"
logger = logging.getLogger(__name__)


@router.get("/capacity")
async def capacity(
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


@router.get("/park-time")
async def park_time(
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
    *,
    start_time_in: datetime | None = None,
    end_time_in: datetime | None = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , REPORTING_ANALYSIS ]
    """

    return APIResponse(
        await report_services.park_time(
            db, start_time_in=start_time_in, end_time_in=end_time_in
        )
    )


@router.get("/referred")
async def avrage_referred(
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
    *,
    start_time_in: datetime,
    end_time_in: datetime,
    timing: report_schemas.Timing = report_schemas.Timing.day,
    zone_id: int | None = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , REPORTING_ANALYSIS ]
    """

    return APIResponse(
        await report_services.get_count_referred(
            db,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
            timing=timing,
            zone_id=zone_id,
        )
    )


@router.get("/max-time-park")
async def max_time_park(
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


@router.get("/count-entrance-exit-zone")
async def count_entrance_exit_zone(
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
    *,
    zone_id: int = None,
) -> APIResponseType[Any]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , REPORTING_ANALYSIS ]
    """

    return APIResponse(
        await report_services.count_entrance_exit_zone(db, zone_id=zone_id)
    )


@router.get("/zones")
async def report_zone(
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

    return APIResponse(await report_services.report_zone(db))
