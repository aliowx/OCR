import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.api.services import parking_services
from app.utils import APIResponse, APIResponseType

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
    return APIResponse(await parking_services.create_line(db, parking_in))


# this endpoint for update status
@router.post("/update_status")
async def update_status(
    parking_in: schemas.ParkingUpdateStatus,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[dict]:

    return APIResponse(await parking_services.update_status(db, parking_in))


# get all status and detail parking
@router.get("/check_status")
async def checking_status(
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:

    return APIResponse(await parking_services.get_status(db))


# this endpoint get all line by camera code
@router.get("/{camera_code}")
async def get_detail_line_by_camera(
    camera_code: str,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.ParkingCreate]:

    return APIResponse(
        await parking_services.get_details_line_by_camera(db, camera_code)
    )


@router.post("/update_price")
async def update_price(
    price_in: schemas.PriceUpdateInParking,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.ParkingCreateLineInDB]:

    return APIResponse(await parking_services.update_price(db, price_in))
