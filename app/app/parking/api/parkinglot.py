import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.api import deps
from app.parking.services import parkinglot as parkinglot_services
from app.utils import APIResponse, APIResponseType

router = APIRouter()
namespace = "parkinglot"
logger = logging.getLogger(__name__)


@router.post("/")
async def create_lines_parkinglot(
    parkinglot_in: schemas.ParkingLotCreate,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Create new line ParkingLot.
    """
    return APIResponse(
        await parkinglot_services.create_line(db, parkinglot_in)
    )


# this endpoint for update status
@router.post("/update_status")
async def update_status(
    parkinglot_in: schemas.ParkingLotUpdateStatus,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[dict]:

    return APIResponse(
        await parkinglot_services.update_status(db, parkinglot_in)
    )


# get all status and detail parkinglot
@router.get("/check_status")
async def checking_status(
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:

    return APIResponse(await parkinglot_services.get_status(db))


# this endpoint get all line by camera code
@router.get("/{camera_code}")
async def get_detail_line_by_camera(
    camera_code: str,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.ParkingLotCreate]:

    return APIResponse(
        await parkinglot_services.get_details_line_by_camera(db, camera_code)
    )


@router.get("/lots/{zone_id}")
async def get_detail_line_by_zone(
    zone_id: int,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[list[schemas.ParkingLotCreate]]:

    return APIResponse(
        await parkinglot_services.get_details_lot_by_zone_id(db, zone_id)
    )


@router.post("/update_price")
async def update_price(
    price_in: schemas.PriceUpdateInParkingLot,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.ParkingLotCreateLineInDB]:

    return APIResponse(await parkinglot_services.update_price(db, price_in))
