import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app import utils
from app.core import exceptions as exc
from app.parking import repo
from app.parking import schemas as parking_schemas

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

    print(parkingzone_input)
    parkingzone = await repo.parkingzone.create(db, obj_in=parkingzone_input)
    return parkingzone
