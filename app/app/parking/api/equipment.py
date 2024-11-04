import logging

from fastapi import APIRouter, Depends, Query
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
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated, Optional
from app.models.base import EquipmentType


router = APIRouter()
namespace = "equipments"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_equipments(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.TECHNICAL_SUPPORT,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    type_eq: Optional[list[EquipmentType]] = Query(None),
    params: schemas.FilterEquipmentsParams = Depends(),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[PaginatedContent[list[schemas.Equipment]]]:
    """
    user access to this [ ADMINISTRATOR , PARKING_MANAGER , TECHNICAL_SUPPORT ]

    EquipmentType = {\n
        CAMERA_ENTRANCE_DOOR = 1\n
        CAMERA_EXIT_DOOR = 2\n
        SENSOR = 3\n
        ROADBLOCK = 4\n
        DISPLAY = 5\n
        CAMERA_DIRECTION_EXIT = 6\n
        CAMERA_DIRECTION_ENTRANCE = 7\n
        KIOSK = 8\n
        PAYMENT_DEVICE = 9\n
        REGIONAL_SWITCH = 10\n
        REGIONAL_COMPUTER = 11\n
        REGIONAL_CONTROLLER = 12\n
        POS = 13\n
        }
    EquipmentStatus = {\n
        HEALTHY = 1\n
        BROKEN = 2\n
        DISCONNECTED = 3\n
        }

    """

    equipments = await equipment_services.get_multi_quipments(
        db, params=params, type_eq=type_eq
    )
    return APIResponse(equipments)


@router.post("/")
async def create_equipment(
    *,
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    equipment_in: schemas.EquipmentCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.Equipment]:
    """
    Create equipment.

    user access to this [ ADMINISTRATOR ]
    EquipmentType = {\n
        CAMERA_ENTRANCE_DOOR = 1\n
        CAMERA_EXIT_DOOR = 2\n
        SENSOR = 3\n
        ROADBLOCK = 4\n
        DISPLAY = 5\n
        CAMERA_DIRECTION_EXIT = 6\n
        CAMERA_DIRECTION_ENTRANCE = 7\n
        KIOSK = 8\n
        PAYMENT_DEVICE = 9\n
        REGIONAL_SWITCH = 10\n
        REGIONAL_COMPUTER = 11\n
        REGIONAL_CONTROLLER = 12\n
        POS = 13\n
        }
    EquipmentStatus = {\n
        HEALTHY = 1\n
        BROKEN = 2\n
        DISCONNECTED = 3\n
        }
    """
    equipment = await equipment_services.create_equipment(
        db, equipment_data=equipment_in
    )
    return APIResponse(equipment)


@router.post("/bulk")
async def create_equipment_bulk(
    *,
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    equipments: list[schemas.EquipmentCreate],
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[list[schemas.Equipment]]:
    """
    Bulk create equipments.

    user access to this [ ADMINISTRATOR ]

    EquipmentType = {\n
        CAMERA_ENTRANCE_DOOR = 1\n
        CAMERA_EXIT_DOOR = 2\n
        SENSOR = 3\n
        ROADBLOCK = 4\n
        DISPLAY = 5\n
        CAMERA_DIRECTION_EXIT = 6\n
        CAMERA_DIRECTION_ENTRANCE = 7\n
        KIOSK = 8\n
        PAYMENT_DEVICE = 9\n
        REGIONAL_SWITCH = 10\n
        REGIONAL_COMPUTER = 11\n
        REGIONAL_CONTROLLER = 12\n
        POS = 13\n
        }
    EquipmentStatus = {\n
        HEALTHY = 1\n
        BROKEN = 2\n
        DISCONNECTED = 3\n
        }

    """
    equipments = await equipment_services.create_equipment_bulk(
        db, equipments=equipments
    )
    return APIResponse(equipments)


@router.put("/{equipment_id}")
async def update_equipment(
    *,
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
    ],
    equipment_id: int,
    db: AsyncSession = Depends(deps.get_db_async),
    equipment_data: schemas.EquipmentUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.Equipment]:
    """
    Update equipment.

    user access to this [ ADMINISTRATOR ]

    EquipmentType = {\n
        CAMERA_ENTRANCE_DOOR = 1\n
        CAMERA_EXIT_DOOR = 2\n
        SENSOR = 3\n
        ROADBLOCK = 4\n
        DISPLAY = 5\n
        CAMERA_DIRECTION_EXIT = 6\n
        CAMERA_DIRECTION_ENTRANCE = 7\n
        KIOSK = 8\n
        PAYMENT_DEVICE = 9\n
        REGIONAL_SWITCH = 10\n
        REGIONAL_COMPUTER = 11\n
        REGIONAL_CONTROLLER = 12\n
        POS = 13\n
        }
    EquipmentStatus = {\n
        HEALTHY = 1\n
        BROKEN = 2\n
        DISCONNECTED = 3\n
        }

    """
    equipment = await equipment_services.update_equipment(
        db, equipment_id=equipment_id, equipment_data=equipment_data
    )
    return APIResponse(equipment)


@router.delete("/{equipment_id}")
async def delete_equipment(
    *,
    _: Annotated[
        bool,
        Depends(RoleChecker(allowed_roles=[UserRoles.ADMINISTRATOR])),
    ],
    equipment_id: int,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.Equipment]:
    """
    Delete equipment.

    user access to this [ ADMINISTRATOR ]

    """
    equipment = await equipment_repo.get(db, id=equipment_id)
    if not equipment:
        raise ServiceFailure(
            detail="Equipment Not Found",
            msg_code=MessageCodes.not_found,
        )
    await equipment_repo.remove(db, id=equipment_id)
    return APIResponse(equipment)
