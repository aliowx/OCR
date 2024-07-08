import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.parking.services import spot as spot_services
from app.utils import APIResponse, APIResponseType, PaginatedContent
from app.parking.schemas import ParamsSpotStatus, SpotsByCamera

router = APIRouter()
namespace = "parkingspot"
logger = logging.getLogger(__name__)


@router.post("/")
async def create_spot(
    spot_in: schemas.SpotCreate,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Create new line Spot.
    """
    return APIResponse(await spot_services.create_line(db, spot_in))


# this endpoint for update status
@router.post("/update_status")
async def update_status_spot(
    spot_in: schemas.SpotUpdateStatus,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[dict]:

    return APIResponse(await spot_services.update_status(db, spot_in))


# get all status and detail spot
@router.get("/check_status")
async def checking_status_spot(
    db: AsyncSession = Depends(deps.get_db_async),
    params: ParamsSpotStatus = Depends(),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:

    return APIResponse(await spot_services.get_status(db, params))


# this endpoint get all line by camera code
@router.get("/{camera_code}")
async def get_detail_line_by_camera(
    camera_code: str,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[SpotsByCamera]:

    return APIResponse(
        await spot_services.get_details_line_by_camera(db, camera_code)
    )


@router.get("/spot/{zone_id}")
async def get_detail_line_by_zone(
    zone_id: int,
    size: int = 100,
    page: int = 1,
    asc: bool = True,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[PaginatedContent[Any]]:

    return APIResponse(
        await spot_services.get_details_spot_by_zone_id(
            db, zone_id, size, page, asc
        )
    )

