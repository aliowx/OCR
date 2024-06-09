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
    parkingzone_input: parking_schemas.ParkingZoneCreate,
) -> parking_schemas.ParkingZone:
    parking = await repo.parking.get(db, id=parkingzone_input.parking_id)
    if not parking:
        main_parking = await repo.parking.get_main_parking(db)
        if not main_parking:
            raise exc.ServiceFailure(
                detail="Parking Not Found",
                msg_code=utils.MessageCodes.not_found,
            )
        parkingzone_input.parking_id = main_parking.id

    parkingzone = await repo.parkingzone.get_by_name(
        db, name=parkingzone_input.name
    )
    if parkingzone:
        raise exc.ServiceFailure(
            detail="Parkingzone with this name already exists",
            msg_code=utils.MessageCodes.duplicate_zone_name,
        )

    parent_zone = None
    if parkingzone_input.parent_id is not None:
        parent_zone = await repo.parkingzone.get(
            db, id=parkingzone_input.parent_id
        )
        if not parent_zone:
            raise exc.ServiceFailure(
                detail="Parking Not Found",
                msg_code=utils.MessageCodes.not_found,
            )

    parkingzone = await repo.parkingzone.create(db, obj_in=parkingzone_input)
    return parkingzone


async def set_price(
    db: AsyncSession,
    parkingzone_id: int,
    zoneprice_data: parking_schemas.SetZonePriceInput,
) -> parking_schemas.ParkingZonePrice:
    zone = await repo.parkingzone_repo.get(db, id=parkingzone_id)
    if not zone:
        raise exc.ServiceFailure(
            detail="ParkingZone Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    price = await price_repo.get(db, id=zoneprice_data.price_id)
    if not price:
        raise exc.ServiceFailure(
            detail="Price Not Found",
            msg_code=utils.MessageCodes.not_found,
        )
    is_duplicate = await repo.parkingzoneprice_repo.get_by_price_priority(
        db, price_id=price.id, priority=zoneprice_data.priority
    )
    if is_duplicate:
        raise exc.ServiceFailure(
            detail="This pricing already exists",
            msg_code=utils.MessageCodes.duplicate_zone_pricing,
        )

    zoneprice_create = parking_schemas.ParkingZonePriceCreate(
        zone_id=zone.id, price_id=price.id, priority=zoneprice_data.priority
    )
    parkingzone_price = await repo.parkingzoneprice_repo.create(
        db, obj_in=zoneprice_create
    )
    return parkingzone_price
