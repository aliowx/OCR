from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.api import deps
from app.core.exceptions import ServiceFailure
from app.parking.repo import zone_repo
from app.parking.schemas import zone as schemas
from app.parking.services import zone as zone_services
from app.utils import APIResponse, APIResponseType, MessageCodes, PaginatedContent
from cache import cache, invalidate
from cache.util import ONE_DAY_IN_SECONDS

router = APIRouter()
namespace = "zones"


@router.get("/")
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_zones(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    params: schemas.ZonePramsFilters = Depends(),
    _: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[PaginatedContent[list[schemas.Zone]]]:
# ):
    """
    Read parking zones.
    """
    zones = await zone_services.read_zone(db, params=params)
    return APIResponse(zones)


@router.get("/{zone_id}")
@cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_zone_by_id(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    zone_id: int,
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Zone]:
    """
    Read zones.
    """
    zone = await zone_repo.get(db, id=zone_id)
    if not zone:
        raise ServiceFailure(
            detail="Zone Not Found",
            msg_code=MessageCodes.not_found,
        )
    return APIResponse(zone)


@router.post("/")
@invalidate(namespace=namespace)
async def create_zone(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    zone_input: schemas.ZoneCreate,
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Zone]:
    """
    Create a zone.
    """
    zone = await zone_services.create_zone(
        db,
        zone_input=zone_input,
    )
    return APIResponse(zone)


@router.post("/{zone_id}/price")
@invalidate(namespace=namespace)
async def set_price_on_parking_zone(
    *,
    zone_id: int,
    zoneprice_data: schemas.SetZonePriceInput,
    db: AsyncSession = Depends(deps.get_db_async),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.ZonePrice]:
    """
    Set price on a zone.
    """
    zone = await zone_services.set_price(
        db,
        zone_id=zone_id,
        zoneprice_data=zoneprice_data,
    )
    return APIResponse(zone)
