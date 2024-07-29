import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.parking.services import spot as spot_services
from app.utils import APIResponse, APIResponseType, PaginatedContent
from app.parking.schemas import ParamsSpotStatus, SpotsByCamera
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated

router = APIRouter()
namespace = "parkingspot"
logger = logging.getLogger(__name__)


@router.post("/")
async def create_spot(
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
    spot_in: schemas.SpotCreate,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Create new line Spot.

    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    return APIResponse(await spot_services.create_spot(db, spot_in))


# this endpoint for update status
@router.post("/update-status")
async def update_status_spot(
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
    spot_in: schemas.SpotUpdateStatus,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[dict]:

    return APIResponse(await spot_services.update_status(db, spot_in))


# get all status and detail spot
@router.get("/check-status")
async def checking_status_spot(
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
    params: ParamsSpotStatus = Depends(),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]

    """

    return APIResponse(await spot_services.get_status(db, params))


@router.get("/find-plate-in-spot")
async def checking_status_spot(
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
    plate: str = None,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    return APIResponse(await spot_services.get_plate_in_spot(db, plate))


# this endpoint get all line by camera code
@router.get("/{camera_serial}")
async def get_detail_line_by_camera(
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
    camera_serial: str,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[SpotsByCamera]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    return APIResponse(
        await spot_services.get_details_spot_by_camera(db, camera_serial)
    )


@router.get("/spot/{zone_id}")
async def get_detail_line_by_zone(
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
    zone_id: int,
    size: int = 100,
    page: int = 1,
    asc: bool = True,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[PaginatedContent[Any]]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    return APIResponse(
        await spot_services.get_details_spot_by_zone_id(
            db, zone_id, size, page, asc
        )
    )
