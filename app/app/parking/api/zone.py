from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.api import deps
from app.core.exceptions import ServiceFailure
from app.parking.repo import zone_repo
from app.parking.schemas import zone as schemasZone
from app.parking.services import zone as zone_services
from app.utils import (
    APIResponse,
    APIResponseType,
    MessageCodes,
    PaginatedContent,
)
from cache import cache, invalidate
from cache.util import ONE_DAY_IN_SECONDS
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated

router = APIRouter()
namespace = "zones"


@router.get("/")
# @cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_zones(
    *,
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.OPERATIONAL_STAFF,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    params: schemasZone.ZonePramsFilters = Depends(),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[PaginatedContent[list[schemasZone.Zone]]]:
    """
    Read parking zones.

    user access to this [ ADMINISTRATOR , PARKING_MANAGER , OPERATIONAL_STAFF ]

    """
    zones = await zone_services.read_zone(db, params=params)

    return APIResponse(zones)


@router.put("/")
# @cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def update_zone(
    *,
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.OPERATIONAL_STAFF,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    zone_id: int,
    params: schemasZone.ZoneUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemasZone.Zone]:
    """
    update parking zones.

    user access to this [ ADMINISTRATOR , PARKING_MANAGER , OPERATIONAL_STAFF ]

    """
    zone = await zone_repo.get(db, id=zone_id)
    if not zone:
        raise ServiceFailure(
            detail="Zone Not Found",
            msg_code=MessageCodes.not_found,
        )
    zone_update = await zone_repo.update(db, db_obj=zone, obj_in=params)

    zone_update = await zone_services.set_children_ancestors_capacity(
        db, zone_update
    )

    return APIResponse(zone_update)


@router.get("/{zone_id}")
# @cache(namespace=namespace, expire=ONE_DAY_IN_SECONDS)
async def read_zone_by_id(
    *,
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.OPERATIONAL_STAFF,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    zone_id: int,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemasZone.Zone]:
    """
    Read zone.

    user access to this [ ADMINISTRATOR , PARKING_MANAGER , OPERATIONAL_STAFF ]

    """

    zone = await zone_repo.get(db, id=zone_id)
    if not zone:
        raise ServiceFailure(
            detail="Zone Not Found",
            msg_code=MessageCodes.not_found,
        )
    zone = await zone_services.set_children_ancestors_capacity(db, zone)

    return APIResponse(zone)


@router.post("/")
@invalidate(namespace=namespace)
async def create_zone(
    *,
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
    zones_in: list[schemasZone.ZoneCreate],
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[list[schemasZone.Zone]]:
    """
    Create sub zone.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , OPERATIONAL_STAFF ]

    """
    zone = await zone_services.create_zone(
        db,
        zones_in=zones_in,
    )
    return APIResponse(zone)


@router.post("/{zone_id}/price")
@invalidate(namespace=namespace)
async def set_price_on_parking_zone(
    *,
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.OPERATIONAL_STAFF,
                ]
            )
        ),
    ],
    zone_id: int,
    zoneprice_data: schemasZone.SetZonePriceInput,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemasZone.ZonePrice]:
    """
    Set price on a zone.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , OPERATIONAL_STAFF ]
    """
    zone = await zone_services.set_price(
        db,
        zone_id=zone_id,
        zoneprice_data=zoneprice_data,
    )
    zone = await zone_services.set_children_ancestors_capacity(db, zone)
    return APIResponse(zone)
