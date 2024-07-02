import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app import utils
from app.core import exceptions as exc
from app.parking import repo
from app.parking import schemas as parking_schemas
from app.pricing.repo import price_repo

logger = logging.getLogger(__name__)


async def create_zone(
    db: AsyncSession,
    zone_input: parking_schemas.ZoneCreate,
) -> parking_schemas.Zone:
    parking = await repo.parking_repo.get(db, id=zone_input.parking_id)
    if not parking:
        main_parking = await repo.parking_repo.get_main_parking(db)
        if not main_parking:
            raise exc.ServiceFailure(
                detail="Parking Not Found",
                msg_code=utils.MessageCodes.not_found,
            )
        zone_input.parking_id = main_parking.id

    zone = await repo.zone_repo.get_by_name(
        db, name=zone_input.name
    )
    if zone:
        raise exc.ServiceFailure(
            detail="zone with this name already exists",
            msg_code=utils.MessageCodes.duplicate_zone_name,
        )

    parent_zone = None
    if zone_input.parent_id is not None:
        parent_zone = await repo.zone_repo.get(
            db, id=zone_input.parent_id
        )
        if not parent_zone:
            raise exc.ServiceFailure(
                detail="Parking Not Found",
                msg_code=utils.MessageCodes.not_found,
            )

    zone = await repo.zone_repo.create(
        db, obj_in=zone_input
    )
    return zone


async def set_price(
    db: AsyncSession,
    zone_id: int,
    zoneprice_data: parking_schemas.SetZonePriceInput,
    commit: bool = True,
) -> parking_schemas.ZonePrice:
    zone = await repo.zone_repo.get(db, id=zone_id)
    if not zone:
        raise exc.ServiceFailure(
            detail="Zone Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    price = await price_repo.get(db, id=zoneprice_data.price_id)
    if not price:
        raise exc.ServiceFailure(
            detail="Price Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    is_duplicate = await repo.zoneprice_repo.pricing_exists(
        db,
        zone_id=zone.id,
        price_id=price.id,
        priority=zoneprice_data.priority,
    )
    if is_duplicate:
        raise exc.ServiceFailure(
            detail="This pricing already exists",
            msg_code=utils.MessageCodes.duplicate_zone_pricing,
        )

    zoneprice_create = parking_schemas.ZonePriceCreate(
        zone_id=zone.id, price_id=price.id, priority=zoneprice_data.priority
    )
    zone_price = await repo.zoneprice_repo.create(
        db, obj_in=zoneprice_create, commit=commit
    )
    return zone_price
