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
from app.bill.repo import bill_repo

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


@router.get("/effective-utilization-rate")
async def get_effective_utilization_rate(
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
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , REPORTING_ANALYSIS ]
    """

    return APIResponse(
        await report_services.effective_utilization_rate(
            db,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
        )
    )


@router.get("/parking-occupancy-by-zone")
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
        await report_services.get_parking_occupancy_by_zone(
            db,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
            timing=timing,
            zone_id=zone_id,
        )
    )


@router.get("/parking-occupancy")
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
        await report_services.get_parking_occupancy(
            db,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
            timing=timing,
            zone_id=zone_id,
        )
    )


@router.get("/records-present")
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
        await crud.record.get_present_in_parking(
            db,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
            timing=timing,
            zone_id=zone_id,
        )
    )


@router.get("/avg-price-per-referred")
async def avg_price_per_referred(
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
    zone_id: int | None = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , REPORTING_ANALYSIS ]
    """

    return APIResponse(
        {
            "avg_price": await bill_repo.avg_price_per_referred(
                db,
                start_time_in=start_time_in,
                end_time_in=end_time_in,
                zone_id=zone_id,
            )
        }
    )


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
    zone_id_in: int | None = None,
    start_time_in: datetime | None = None,
    end_time_in: datetime | None = None,
) -> APIResponseType[Any]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , REPORTING_ANALYSIS ]
    """

    return APIResponse(
        await report_services.count_entrance_exit_zone(
            db,
            zone_id_in=zone_id_in,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
        )
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


@router.get("/bill")
async def report_bill(
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
    zone_id: int | None = None,
    start_time_in: datetime | None = None,
    end_time_in: datetime | None = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , REPORTING_ANALYSIS ]
    """

    return APIResponse(
        await report_services.report_bill(
            db,
            zone_id=zone_id,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
        )
    )


@router.get("/bill-by-timing")
async def report_bill_by_timing(
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
    timing: report_schemas.Timing = report_schemas.Timing.day,
    zone_id: int | None = None,
    start_time_in: datetime,
    end_time_in: datetime,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , REPORTING_ANALYSIS ]
    """

    return APIResponse(
        await report_services.report_bill_by_timing(
            db,
            timing=timing,
            zone_id=zone_id,
            start_time_in=start_time_in,
            end_time_in=end_time_in,
        )
    )
