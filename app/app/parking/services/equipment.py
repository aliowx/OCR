from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ServiceFailure
from app.parking.models import Equipment
from app.parking.repo import equipment_repo, parking_repo, parkingzone_repo
from app.parking.schemas import equipment as schemas
from app.utils import MessageCodes, PaginatedContent


async def read_equipments(
    db: AsyncSession, params: schemas.ReadEquipmentsParams
) -> PaginatedContent[list[schemas.Equipment]]:
    equipments, total_count = await equipment_repo.get_multi_with_filters(
        db, filters=params.db_filters
    )
    return PaginatedContent(
        data=equipments,
        total_count=total_count,
        size=params.size,
        page=params.page,
    )


async def create_equipment(
    db: AsyncSession,
    equipment_data: schemas.EquipmentCreate,
    commit: bool = True,
) -> Equipment:
    if equipment_data.parking_id:
        parking = await parking_repo.get(db, id=equipment_data.parking_id)
    else:
        parking = await parking_repo.get_main_parking(db)
    if not parking:
        raise ServiceFailure(
            detail="Parking Not Found",
            msg_code=MessageCodes.not_found,
        )
    parkingzone = await parkingzone_repo.get(db, id=equipment_data.zone_id)
    if not parkingzone:
        raise ServiceFailure(
            detail="ParkingZone  Not Found",
            msg_code=MessageCodes.not_found,
        )
    params = schemas.ReadEquipmentsParams(
        parking_id=equipment_data.parking_id,
        ip_address=equipment_data.ip_address,
    )
    ip_address_check = await read_equipments(db, params=params)
    if ip_address_check.total_count:
        raise ServiceFailure(
            detail="Duplicate ip address",
            msg_code=MessageCodes.duplicate_ip_address,
        )
    params = params.model_copy(
        update={
            "ip_address": None,
            "serial_number": equipment_data.serial_number,
            "equipment_type": equipment_data.equipment_type,
        }
    )
    serial_number_check = await read_equipments(db, params=params)
    if serial_number_check.total_count:
        raise ServiceFailure(
            detail="Duplicate equipment serial number",
            msg_code=MessageCodes.duplicate_serial_number,
        )
    equipment = await equipment_repo.create(
        db, obj_in=equipment_data, commit=commit
    )

    return equipment


async def create_equipment_bulk(
    db: AsyncSession, equipments: list[schemas.EquipmentCreate]
) -> list[Equipment]:
    created_equipments = []
    for eq in equipments:
        equipment = await create_equipment(db, equipment_data=eq, commit=False)
        created_equipments.append(equipment)
    await db.commit()
    return created_equipments


async def update_equipment(
    db: AsyncSession,
    equipment_id: int,
    equipment_data: schemas.EquipmentUpdate,
) -> Equipment:
    equipment = await equipment_repo.get(db, id=equipment_id)
    if not equipment:
        raise ServiceFailure(
            detail="Equipment Not Found",
            msg_code=MessageCodes.not_found,
        )

    if equipment_data.parking_id is not None:
        parking = await parking_repo.get(db, id=equipment_data.parking_id)
        if not parking:
            raise ServiceFailure(
                detail="Parking Not Found",
                msg_code=MessageCodes.not_found,
            )
    if equipment_data.zone_id is not None:
        parkingzone = await parkingzone_repo.get(db, id=equipment_data.zone_id)
        if not parkingzone:
            raise ServiceFailure(
                detail="ParkingZone Not Found",
                msg_code=MessageCodes.not_found,
            )

    if equipment_data.ip_address:
        params = schemas.ReadEquipmentsParams(
            parking_id=equipment_data.parking_id,
            ip_address=equipment_data.ip_address,
            size=1,
        )
        ip_address_check = await read_equipments(db, params=params)
        if ip_address_check.data and equipment != ip_address_check.data[0]:
            raise ServiceFailure(
                detail="Duplicate ip address",
                msg_code=MessageCodes.duplicate_ip_address,
            )

    if equipment_data.serial_number:
        params = schemas.ReadEquipmentsParams(
            parking_id=equipment_data.parking_id,
            serial_number=equipment_data.serial_number,
            equipment_type=equipment_data.equipment_type.value,
            size=1,
        )
        serial_number_check = await read_equipments(db, params=params)
        if (
            serial_number_check.data
            and equipment != serial_number_check.data[0]
        ):
            raise ServiceFailure(
                detail="Duplicate equipment serial number",
                msg_code=MessageCodes.duplicate_serial_number,
            )
    if equipment_data.additional_data:
        current_additional_data = equipment.additional_data.copy()
        current_additional_data.update(equipment_data.additional_data)
        equipment.additional_data = current_additional_data
    equipment = await equipment_repo.update(
        db, obj_in=equipment_data, db_obj=equipment
    )

    return equipment
