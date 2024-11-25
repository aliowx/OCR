from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import ServiceFailure
from app.parking.models import Equipment
from app.core.config import settings
from app.parking.repo import equipment_repo, zone_repo
from app.notifications.repo import notifications_repo
from app.notifications.schemas import NotificationsCreate, TypeNotice
from app.parking import schemas
from app.utils import MessageCodes, PaginatedContent
from typing import Optional
from app import models
from cache.redis import redis_connect_async
from app.jobs.celery.celeryworker_pre_start import redis_client
import requests
import rapidjson


async def get_multi_quipments(
    db: AsyncSession,
    params: schemas.FilterEquipmentsParams,
    type_eq: Optional[list[models.base.EquipmentType]] = None,
) -> PaginatedContent[list[schemas.Equipment]]:

    equipments, total_count = await equipment_repo.get_multi_with_filters(
        db, params=params, type_eq=type_eq
    )
    # equipments[0] --> equipment
    # equipments[1] --> zone_name
    resualt = []
    for eq, zone in equipments:
        eq.zone_name = zone
        resualt.append(eq)
    return PaginatedContent(
        data=resualt,
        total_count=total_count,
        size=params.size,
        page=params.page,
    )


async def create_equipment(
    db: AsyncSession,
    equipment_data: schemas.EquipmentCreate,
    commit: bool = True,
) -> Equipment:
    if equipment_data.zone_id is not None:
        zone = await zone_repo.get(db, id=equipment_data.zone_id)
        if not zone:
            raise ServiceFailure(
                detail="Zone  Not Found",
                msg_code=MessageCodes.not_found,
            )
    params = schemas.FilterEquipmentsParams(
        ip_address=equipment_data.ip_address,
    )
    ip_address_check = await get_multi_quipments(db, params)
    if ip_address_check.total_count:
        raise ServiceFailure(
            detail="Duplicate ip address",
            msg_code=MessageCodes.duplicate_ip_address,
        )
    params = schemas.FilterEquipmentsParams(
        tag=equipment_data.tag,
    )
    tag_check = await get_multi_quipments(db, params)
    if tag_check.total_count:
        raise ServiceFailure(
            detail="Duplicate tag",
            msg_code=MessageCodes.duplicate_name,
        )
    params = schemas.FilterEquipmentsParams(
        ip_address=equipment_data.ip_address,
    )
    ip_address_check = await get_multi_quipments(db, params)
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
    serial_number_check = await get_multi_quipments(db, params)
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
        ip_address_check = (await get_multi_quipments(db, params=params)).data
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
        serial_number_check = (
            await get_multi_quipments(db, params=params)
        ).data
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
        tag_check = (await get_multi_quipments(db, params=params)).data
        if tag_check:
            if tag_check[0].tag and equipment.tag != tag_check[0].tag:
                raise ServiceFailure(
                    detail="Duplicate equipment tag",
                    msg_code=MessageCodes.duplicate_name,
                )
    if equipment_data.additional_data is not None:
        current_additional_data = equipment.additional_data.copy()
        current_additional_data.update(equipment_data.additional_data)
        equipment.additional_data = current_additional_data
    equipment = await equipment_repo.update(
        db, obj_in=equipment_data, db_obj=equipment
    )

    return equipment


async def health_check_equipment(
    db: AsyncSession,
    *,
    equipment_id: int,
    equipment_status: models.base.EquipmentStatus,
):

    get_equipment = await equipment_repo.get(db, id=equipment_id)

    _get_status = get_equipment.equipment_status

    if not get_equipment:
        raise ServiceFailure(
            detail="equipment not found",
            msg_code=MessageCodes.not_found,
        )

    get_equipment.equipment_status = equipment_status
    update_equipment = await equipment_repo.update(db, db_obj=get_equipment)

    status = update_equipment.equipment_status
    match status:
        case models.base.EquipmentStatus.HEALTHY:
            status = "سالم"
        case models.base.EquipmentStatus.DISCONNECTED:
            status = "قطع"
        case models.base.EquipmentStatus.BROKEN:
            status = "خراب"

    redis_connected = await redis_connect_async()
    notification = await notifications_repo.create(
        db,
        obj_in=NotificationsCreate(
            text=f"دوربین {update_equipment.tag} {status} است",
            type_notice=TypeNotice.equipment,
        ),
    )
    redis_client.publish(
        "notifications",
        rapidjson.dumps(f"دوربین {update_equipment.tag} {status} است"),
    )
    for phone in settings.PHONE_LIST_REPORT_HEALTH_CHECK_EQUIPMENT:

        check = await redis_connected.get(phone)
        if not check or _get_status != update_equipment.equipment_status:
            await redis_connected.set(phone, phone, ex=3600)
            params_sending = {
                "phoneNumber": phone,
                "textMessage": f"دوربین {update_equipment.tag} {status} است",
            }
            send_code = requests.post(
                settings.URL_SEND_SMS,
                params=params_sending,
            )
    return update_equipment
