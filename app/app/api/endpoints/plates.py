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
from app.parking.repo import camera_repo

router = APIRouter()
namespace = "plates"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_plates(
    db: AsyncSession = Depends(deps.get_db_async),
    params: schemas.ParamsPlates = Depends(),
) -> APIResponseType[schemas.GetPlates]:
    """
    All plates.
    """
    camera_id = None
    if params.input_camera_code is not None:
        camera_id = await camera_repo.one_camera(
            db, input_camera_code=params.input_camera_code
        ).id
        params.input_camera_id = camera_id
    plates = await crud.plate.find_plates(db, params=params)
    for i in range(len(plates[0])):
        plates[0][i].fancy = (
            f"{plates[0][i].plate_image_id}/{plates[0][i].lpr_image_id}"
        )

    return APIResponse(
        schemas.GetPlates(items=plates[0], all_items_count=plates[1])
    )


@router.get("/by_record")
async def read_plates_by_record(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    record_id: int,
    skip: int = 0,
    limit: int = 100,
) -> APIResponseType[schemas.GetPlates]:
    """
    all plates for one record.
    """
    plates = await crud.plate.get_by_record(
        db, record_id=record_id, skip=skip, limit=limit
    )
    for i in range(len(plates)):
        plates[i].fancy = (
            f"{plates[i].plate_image_id}/{plates[i].lpr_image_id}"
        )

    return APIResponse(
        schemas.GetPlates(items=plates, all_items_count=len(plates))
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
    plate.fancy = f"{plate.plate_image_id}/{plate.lpr_image_id}"
    return APIResponse(plate)
