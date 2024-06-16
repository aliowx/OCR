import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.api import deps
from app.core.exceptions import ServiceFailure
from app.parking.repo import equipment_repo
from app.parking.schemas import equipment as schemas
from app.parking.services import equipment as equipment_services
from app.utils import (
    APIResponse,
    APIResponseType,
    MessageCodes,
    PaginatedContent,
)

router = APIRouter()
namespace = "equipments"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_equipments(
    db: AsyncSession = Depends(deps.get_db_async),
    params: schemas.ReadEquipmentsParams = Depends(),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[PaginatedContent[list[schemas.Equipment]]]:
    """
    Read equipments.
    """
    equipments = await equipment_services.read_equipments(db, params=params)
    return APIResponse(equipments)


@router.post("/")
async def create_equipment(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    equipment_in: schemas.EquipmentCreate,
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Equipment]:
    """
    Create equipment.
    """
    equipment = await equipment_services.create_equipment(
        db, equipment_data=equipment_in
    )
    return APIResponse(equipment)


@router.post("/bulk")
async def create_equipment_bulk(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    equipments: list[schemas.EquipmentCreate],
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[list[schemas.Equipment]]:
    """
    Bulk create equipments.
    """
    equipments = await equipment_services.create_equipment_bulk(
        db, equipments=equipments
    )
    return APIResponse(equipments)


@router.put("/{equipment_id}")
async def update_equipment(
    *,
    equipment_id: int,
    db: AsyncSession = Depends(deps.get_db_async),
    equipment_data: schemas.EquipmentUpdate,
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Equipment]:
    """
    Update equipment.
    """
    equipment = await equipment_services.update_equipment(
        db, equipment_id=equipment_id, equipment_data=equipment_data
    )
    return APIResponse(equipment)


@router.delete("/{equipment_id}")
async def delete_equipment(
    *,
    equipment_id: int,
    db: AsyncSession = Depends(deps.get_db_async),
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Equipment]:
    """
    Delete equipment.
    """
    equipment = await equipment_repo.get(db, id=equipment_id)
    if not equipment:
        raise ServiceFailure(
            detail="Equipment Not Found",
            msg_code=MessageCodes.not_found,
        )
    await equipment_repo.remove(db, id=equipment_id)
    return APIResponse(equipment)
