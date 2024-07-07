import logging
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas, utils
from app.api import deps
from app.core import exceptions as exc
from app.core.celery_app import celery_app
from app.utils import APIResponse, APIResponseType
from app.parking.repo import equipment_repo
from app.utils import PaginatedContent
from app.parking.schemas.equipment import (
    ReadEquipmentsFilter,
)

router = APIRouter()
namespace = "plates"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_plates(
    db: AsyncSession = Depends(deps.get_db_async),
    params: schemas.ParamsPlates = Depends(),
) -> APIResponseType[PaginatedContent[list[schemas.Plate]]]:
    """
    All plates.
    """
    camera_id = None
    if params.input_camera_serial is not None:
        camera_id, total_count = await equipment_repo.get_multi_with_filters(
            db,
            filters=ReadEquipmentsFilter(
                serial_number__eq=params.input_camera_serial
            ),
        )
        params.input_camera_id = camera_id.id
    plates = await crud.plate.find_plates(db, params=params)

    return APIResponse(
        PaginatedContent(
            data=plates[0],
            total_count=plates[1],
            page=params.page,
            size=params.size,
        )
    )


@router.post("/")
async def create_plate(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    plate_in: schemas.PlateCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
    """
    Create new item.
    """
    result = celery_app.send_task(
        "add_plates",
        args=[jsonable_encoder(plate_in)],
    )

    return APIResponse(f"This id task => {result.task_id}")


@router.get("/{id}")
async def read_plate(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
) -> APIResponseType[schemas.Plate]:
    """
    Get plate by ID.
    """
    plate = await crud.plate.get(db=db, id=id)
    if not plate:
        raise exc.ServiceFailure(
            detail="not exist.",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(plate)
