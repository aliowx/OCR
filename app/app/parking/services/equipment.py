from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.encoders import jsonable_encoder
from app.core.exceptions import ServiceFailure
from app.parking.models import Equipment
from app.parking.repo import equipment_repo, zone_repo
from app.parking.schemas import equipment as schemas
from app.parking.schemas import Zone as schemasZone
from app.utils import MessageCodes, PaginatedContent
from pydantic import TypeAdapter


async def get_multi_quipments(
    db: AsyncSession, params: schemas.FilterEquipmentsParams
):
    equipments, total_count = await equipment_repo.get_multi_with_filters(
        db, params=params
    )
    return [equipments, total_count]


async def read_equipments(
    db: AsyncSession, params: schemas.FilterEquipmentsParams
) -> PaginatedContent[list[schemas.Equipment]]:
    equipments, total_count = await get_multi_quipments(db, params)
    adapter = TypeAdapter(schemasZone)
    for zone in equipments:
        zone_detail = await zone_repo.get(db, id=zone.zone_id)
        if zone_detail:
            zone.zone_detail = jsonable_encoder(
                adapter.validate_python(zone_detail, from_attributes=True)
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
    zone = await zone_repo.get(db, id=equipment_data.zone_id)
    if not zone:
        raise ServiceFailure(
            detail="Zone  Not Found",
            msg_code=MessageCodes.not_found,
        )
    params = schemas.FilterEquipmentsParams(
        ip_address=equipment_data.ip_address,
    )
    ip_address_check, total_count_ip = await get_multi_quipments(db, params)
    if total_count_ip:
        raise ServiceFailure(
            detail="Duplicate ip address",
            msg_code=MessageCodes.duplicate_ip_address,
        )
    params = schemas.FilterEquipmentsParams(
        tag=equipment_data.tag,
    )
    tag_check, total_count_tag = await get_multi_quipments(db, params)
    if total_count_tag:
        raise ServiceFailure(
            detail="Duplicate tag",
            msg_code=MessageCodes.duplicate_name,
        )
    params = schemas.FilterEquipmentsParams(
        ip_address=equipment_data.ip_address,
    )
    ip_address_check, total_count_ip = await get_multi_quipments(db, params)
    if total_count_ip:
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
    serial_number_check, total_count_serial_number = await get_multi_quipments(
        db, params
    )
    if total_count_serial_number:
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

    if equipment_data.zone_id is not None:
        zone = await zone_repo.get(db, id=equipment_data.zone_id)
        if not zone:
            raise ServiceFailure(
                detail="Zone Not Found",
                msg_code=MessageCodes.not_found,
            )

    if equipment_data.ip_address is not None:
        params = schemas.FilterEquipmentsParams(
            ip_address=equipment_data.ip_address,
            size=1,
        )
        ip_address_check, total_count = await get_multi_quipments(
            db, params=params
        )
        if ip_address_check:
            if (
                ip_address_check[0].ip_address
                and equipment.ip_address != ip_address_check[0].ip_address
            ):
                raise ServiceFailure(
                    detail="Duplicate ip address",
                    msg_code=MessageCodes.duplicate_ip_address,
                )

    if equipment_data.serial_number is not None:
        params = schemas.FilterEquipmentsParams(
            serial_number=equipment_data.serial_number,
            size=1,
        )
        serial_number_check, total_count = await get_multi_quipments(
            db, params=params
        )
        if serial_number_check:
            if (
                serial_number_check[0].serial_number
                and equipment.serial_number
                != serial_number_check[0].serial_number
            ):
                raise ServiceFailure(
                    detail="Duplicate equipment serial number",
                    msg_code=MessageCodes.duplicate_serial_number,
                )
    if equipment_data.tag is not None:
        params = schemas.FilterEquipmentsParams(
            tag=equipment_data.tag,
            size=1,
        )
        tag_check, total_count = await get_multi_quipments(
            db, params=params
        )
        if total_count:
            if (
                tag_check[0].tag
                and equipment.tag
                != tag_check[0].tag
            ):
                raise ServiceFailure(
                    detail="Duplicate equipment tag",
                    msg_code=MessageCodes.duplicate_name,
                )
    if equipment_data.additional_data:
        current_additional_data = equipment.additional_data.copy()
        current_additional_data.update(equipment_data.additional_data)
        equipment.additional_data = current_additional_data
    equipment = await equipment_repo.update(
        db, obj_in=equipment_data, db_obj=equipment
    )

    return equipment
