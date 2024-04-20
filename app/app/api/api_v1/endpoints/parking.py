import logging
from app.utils import APIResponse, APIResponseType
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, schemas
from app.api import deps
from app.api.api_v1.services import parking_services

router = APIRouter()
namespace = "parking"
logger = logging.getLogger(__name__)


@router.post("/")
async def create_lines_parking(
    parking_in: schemas.ParkingCreate,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Create new line Parking.
    """
    parking = await parking_services.create_line(db, parking_in)
    # this schemas show result
    return APIResponse(parking)


# this endpoint for update status
@router.post("/update_status")
async def update_status(
    parking_in: schemas.ParkingUpdateStatus,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[dict]:

    update_status = await parking_services.update_status(db, parking_in)
    return APIResponse(update_status)


# get all status and detail parking
@router.get("/check_status")
async def checking_status(
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:

    parking_details = await parking_services.get_status(db)
    return APIResponse(parking_details)


# this endpoint get all line by camera code
@router.get("/{camera_code}")
async def get_detail_line_by_camera(
    camera_code: str,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.ParkingCreate]:

    # check camera exist
    result = await parking_services.get_details_line_by_camera(db, camera_code)
    return APIResponse(result)
