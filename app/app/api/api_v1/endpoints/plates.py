import logging
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, models, schemas, utils
from app.api import deps
from cache.redis import redis_client
from app.core.celery_app import celery_app
from app.utils import APIResponse, APIResponseType
from app import exceptions as exc

router = APIRouter()
namespace = "plates"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_plates(
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 100,
) -> APIResponseType[schemas.GetPlates]:
    """
    All plates.
    """
    plates = await crud.plate.get_multi(db, skip=skip, limit=limit)
    for i in range(len(plates)):
        plates[i].fancy = f"{plates[i].big_image_id}/{plates[i].lpr_id}"
    all_items_count = redis_client.get("plates_count")
    if all_items_count is None:
        all_items_count = await crud.plate.count(db=db)
    return APIResponse(
        schemas.GetPlates(items=plates, all_items_count=all_items_count)
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
        plates[i].fancy = f"{plates[i].big_image_id}/{plates[i].lpr_id}"

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
    plate.fancy = f"{plate.big_image_id}/{plate.lpr_id}"
    return APIResponse(plate)


@router.get("/find/search")
async def findplates(
    db: AsyncSession = Depends(deps.get_db_async),
    input_ocr: str = None,
    input_camera_code: str = None,
    input_time_min: datetime = None,
    input_time_max: datetime = None,
    skip: int = 0,
    limit: int = 100,
) -> APIResponseType[schemas.GetPlates]:
    """
    search plates
    """
    camera_id = None
    if input_camera_code is not None:
        camera = await crud.camera.one_camera(
            db, input_camera_code=input_camera_code
        )
        camera_id = camera.id

    plates = await crud.plate.find_plates(
        db,
        input_ocr=input_ocr,
        input_camera_id=camera_id,
        input_time_min=input_time_min,
        input_time_max=input_time_max,
        skip=skip,
        limit=limit,
    )
    for i in range(plates[1]):
        plates[0][
            i
        ].fancy = f"{plates[0][i].big_image_id}/{plates[0][i].lpr_id}"

    return APIResponse(
        schemas.GetPlates(items=plates[0], all_items_count=plates[1])
    )
