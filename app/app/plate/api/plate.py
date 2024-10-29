import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, utils
from app.plate import schemas
from app.plate.repo import plate_repo
from app.api import deps
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType, PaginatedContent
from app.plate.services import plate as ServicePlate

from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated

router = APIRouter()
namespace = "plate"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_plate(
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
    current_user: models.User = Depends(deps.get_current_active_superuser),
    *,
    params: schemas.ParamsPlate = Depends(),
) -> APIResponseType[PaginatedContent[list[schemas.PlateList]]]:
    """
    Retrieve plate.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    plate, total_count = await ServicePlate.get_multi_plate_by_filter(
        db, params=params
    )
    return APIResponse(
        PaginatedContent(
            data=plate,
            total_count=total_count,
            size=params.size,
            page=params.page,
        )
    )


@router.post("/")
async def create_Plate(
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
    *,
    plate_in: schemas.PlateCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.PlateList]:
    """
    Create new plate.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    plate, count = await plate_repo.get_multi_by_filter(
        db, params=schemas.ParamsPlate(input_plate=plate_in.plate)
    )
    if count > 0:
        raise exc.ServiceFailure(
            detail="plate already",
            msg_code=utils.MessageCodes.not_found,
        )
    plate = await plate_repo.create(db, obj_in=plate_in.model_dump())
    return APIResponse(plate)


@router.get("/{id}")
async def read_plate_by_id(
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
    current_user: models.User = Depends(deps.get_current_active_user),
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    id: int,
) -> APIResponseType[schemas.PlateList]:
    """
    Get a specific Plate by id.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    plate = await plate_repo.get(db, id=id)
    if not plate:
        raise exc.ServiceFailure(
            detail="plate not found",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(plate)


@router.delete("/{id}")
async def delete_plate(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                ]
            )
        ),
    ],
    current_user: models.User = Depends(deps.get_current_active_superuser),
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    id: int,
) -> APIResponseType[schemas.PlateList]:
    """
    delete plate.
    user access to this [ ADMINISTRATOR ]
    """
    plate = await plate_repo.get(db, id=id)
    if not plate:
        raise exc.ServiceFailure(
            detail="plate not found",
            msg_code=utils.MessageCodes.not_found,
        )
    del_plate = await plate_repo.remove(db, id=plate.id, commit=True)
    return APIResponse(del_plate)


@router.put("/{id}")
async def update_plate(
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
    id: int,
    plate_in: schemas.PlateUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.PlateList]:
    """
    Update a plate.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    plate = await plate_repo.get(db, id=id)
    if not plate:
        raise exc.ServiceFailure(
            detail="The plate does't exist in the system",
            msg_code=utils.MessageCodes.not_found,
        )
    plate = await plate_repo.update(
        db, db_obj=plate, obj_in=plate_in.model_dump()
    )
    return APIResponse(plate)
