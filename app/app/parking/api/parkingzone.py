from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.api import deps
from app.core.exceptions import ServiceFailure
from app.parking.repo import parkingzone_repo
from app.parking.schemas import parkingzone as schemas
from app.parking.services import parkingzone as parkingzone_services
from app.utils import APIResponse, APIResponseType, MessageCodes
from cache import cache, invalidate
from cache.util import ONE_DAY_IN_SECONDS

router = APIRouter()
namespace = "parkingzones"


@router.get("/")
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_parkingzones(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 100,
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[list[schemas.ParkingZone]]:
    """
    Read parking zones.
    """
    parkingzones = await parkingzone_repo.get_multi(db, limit=limit, skip=skip)
    return APIResponse(parkingzones)


@router.get("/{zone_id}")
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_parkingzone_by_id(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    zone_id: int,
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.ParkingZone]:
    """
    Read parking zones.
    """
    parkingzone = await parkingzone_repo.get(db, id=zone_id)
    if not parkingzone:
        raise ServiceFailure(
            detail="ParkingZone Not Found",
            msg_code=MessageCodes.not_found,
        )
    return APIResponse(parkingzone)


@router.post("/")
@invalidate(namespace=namespace)
async def create_parkingzone(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    parkingzone_input: schemas.ParkingZoneCreate,
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.ParkingZone]:
    """
    Create a parking zone.
    """
    parkingzone = await parkingzone_services.create_zone(
        db,
        parkingzone_input=parkingzone_input,
    )
    return APIResponse(parkingzone)


@router.post("/{zone_id}/price")
@invalidate(namespace=namespace)
async def set_price_on_parking_zone(
    *,
    zone_id: int,
    zoneprice_data: schemas.SetZonePriceInput,
    db: AsyncSession = Depends(deps.get_db_async),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.ParkingZonePrice]:
    """
    Set price on a parking zone.
    """
    parkingzone = await parkingzone_services.set_price(
        db,
        parkingzone_id=zone_id,
        zoneprice_data=zoneprice_data,
    )
    return APIResponse(parkingzone)
