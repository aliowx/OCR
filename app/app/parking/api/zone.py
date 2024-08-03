from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.api import deps
from app.core.exceptions import ServiceFailure
from app.parking.repo import zone_repo
from app.parking.schemas import zone as schemas
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
from pydantic import TypeAdapter

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
    params: schemas.ZonePramsFilters = Depends(),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[PaginatedContent[list[schemas.Zone]]]:
    """
    Read parking zones.

    user access to this [ ADMINISTRATOR , PARKING_MANAGER , OPERATIONAL_STAFF ]

    """
    # adapter = TypeAdapter(schemas.Zone)
    zones = await zone_services.read_zone(db, params=params)
    # zones1 = adapter.validate_python(zones.data, from_attributes=True)
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
    params: schemas.ZoneUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.Zone]:
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
) -> APIResponseType[schemas.Zone]:
    """
    Read zone.

    user access to this [ ADMINISTRATOR , PARKING_MANAGER , OPERATIONAL_STAFF ]

    """
    # this solution fixes maximum recursion depth exceeded error in jsonable_encoder
    # create model schema from orm object before sending it to jsonable_encoder
    # adapter = TypeAdapter(schemas.Zone)

    zone = await zone_repo.get(db, id=zone_id)
    if not zone:
        raise ServiceFailure(
            detail="Zone Not Found",
            msg_code=MessageCodes.not_found,
        )

    # zone = adapter.validate_python(zone, from_attributes=True)
    return APIResponse(zone)


@router.post("/")
@invalidate(namespace=namespace)
async def create_parent_zone(
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
    zone_input: schemas.ZoneCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.Zone]:
    """
    Create a zone.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , OPERATIONAL_STAFF ]

    """
    zone = await zone_services.create_zone(
        db,
        zone_input=zone_input,
    )
    return APIResponse(zone)


@router.post("/bulk-sub-zone")
@invalidate(namespace=namespace)
async def create_sub_zone(
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
    zone_input: schemas.SubZoneCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[list[schemas.Zone]]:
    """
    Create sub zone.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , OPERATIONAL_STAFF ]

    """
    zone = await zone_services.create_sub_zone(
        db,
        zone_input=zone_input,
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
    zoneprice_data: schemas.SetZonePriceInput,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.ZonePrice]:
    """
    Set price on a zone.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , OPERATIONAL_STAFF ]
    """
    zone = await zone_services.set_price(
        db,
        zone_id=zone_id,
        zoneprice_data=zoneprice_data,
    )
    return APIResponse(zone)
