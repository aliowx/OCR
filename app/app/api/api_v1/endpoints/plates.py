from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, models, schemas
from app.api import deps
from cache.redis import redis_client
from app.core.celery_app import celery_app
import logging

router = APIRouter()
namespace = "plates"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_plates(
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve plates.
    """
    plates = await crud.plate.get_multi(db, skip=skip, limit=limit)
    # for i in range(len(plates)):
    #     plates[i].fancy = f"{plates[i].big_image_id}/{plates[i].lpr_id}"
    # all_items_count = crud.plate.get_count(db)
    # all_items_count = redis_client.get("plates_count")
    # if all_items_count is None:
    #     all_items_count = await crud.plate.get_count(db=db)
    return schemas.GetPlates(items=plates, all_items_count=1)


@router.get("/by_record", response_model=schemas.GetPlates)
async def read_plates_by_record(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    record_id: int,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve plates.
    """
    plates = await crud.plate.get_by_record(
        db, record_id=record_id, skip=skip, limit=limit
    )
    for i in range(len(plates)):
        plates[i].fancy = f"{plates[i].big_image_id}/{plates[i].lpr_id}"
    # all_items_count = crud.plate.get_count(db)
    all_items_count = len(plates)
    return schemas.GetPlates(items=plates, all_items_count=all_items_count)


@router.get("/firstrecords/", response_model=List[schemas.Plate])
async def read_plates_firstrecords(
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve plates.
    """
    plates = await crud.plate.get_multi_filter(
        db, record_number=0, skip=skip, limit=limit
    )
    for i in range(len(plates)):
        plates[i].fancy = f"{plates[i].big_image_id}/{plates[i].lpr_id}"
    return plates


@router.get("/checkoperatory/", response_model=List[schemas.Plate])
async def read_records_checkoperatory(
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve unchecked plates.
    """
    plates = await crud.plate.get_multi_filter(
        db, ocr_checked=False, skip=skip, limit=limit
    )
    for i in range(len(plates)):
        plates[i].fancy = f"{plates[i].big_image_id}/{plates[i].lpr_id}"
    return plates


@router.post("/", response_model=Any)
async def create_plate(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    plate_in: schemas.PlateCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new item.
    """
    current_user_dict = jsonable_encoder(current_user)

    logger.info(f"create plate current_user: {current_user_dict}")
    result = celery_app.send_task(
        "app.worker.add_plate",
        args=[jsonable_encoder(plate_in), current_user_dict],
    )

    return result.task_id
    # plate = crud.plate.create_with_owner(
    #     db=db, obj_in=plate_in, owner_id=current_user.id
    # )

    # # if settings.CPAYTAX_USERNAME is not None and plate.record_number == 0:
    # celery_app.send_task(
    #     "app.worker.update_record", args=[plate.id, current_user_dict]
    # )
    # return plate


# @router.post("/all_together", response_model=Any)
# async def create_plate_together(
#     *,
#     db: AsyncSession = Depends(deps.get_db_async),
#     plates_in: schemas.PlatesToghetherCreate,
#     current_user: models.User = Depends(deps.get_current_active_user),
# ) -> Any:
#     """
#     Create new plate.
#     """
#     current_user_dict = jsonable_encoder(current_user)

#     logger.info(f"create plates together current_user: {current_user_dict}")
#     logger.info(f"create plates together current_user: {plates_in.plates}")

#     result = celery_app.send_task(
#         "app.worker.add_plates",
#         args=[jsonable_encoder(plates_in), current_user_dict],
#     )

#     return result.task_id

# plates = crud.plate.create_with_image(
#     db=db, obj_in=plates_in, owner_id=current_user.id
# )

# for plate in plates:
#     # if settings.CPAYTAX_USERNAME is not None and plate.record_number == 0:
#     celery_app.send_task(
#         "app.worker.update_record",
#         args=[jsonable_encoder(plate), current_user_dict],
#     )
# return plates


@router.put("/{id}", response_model=schemas.Plate)
async def update_plate(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
    plate_in: schemas.PlateUpdate,
) -> Any:
    """
    Update a Plate.
    """
    plate = await crud.plate.get(db=db, id=id)
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    plate = await crud.plate.update(db=db, db_obj=plate, obj_in=plate_in)
    return plate


# @router.put("/checkoperatory/{id}", response_model=schemas.Plate)
# async def update_plate_ocrchecked(
#     *,
#     db: AsyncSession = Depends(deps.get_db_async),
#     id: int,
#     plate_in: schemas.PlateUpdateCheckOperatory,
# ) -> Any:
#     """
#     Update a Plate's OCR.
#     """
#     plate = await crud.plate.get(db=db, id=id)
#     if not plate:
#         raise HTTPException(status_code=404, detail="Plate not found")
#     if plate.additional_data is None:
#         plate.additional_data = {}
#     plate.additional_data["checkoperatory"] = plate_in.additional_data
#     if "checkoperatory_times" not in plate.additional_data:
#         plate.additional_data["checkoperatory_times"] = []
#     plate.additional_data["checkoperatory_times"].append(datetime.now().isoformat())
#     plate_in.additional_data = plate.additional_data
#     logger.info(plate_in.ocr_checked)
#     logger.info(plate_in.additional_data)
#     plate = await crud.plate.update_checkoperatory(db=db, db_obj=plate, obj_in=plate_in)
#     return plate


@router.get("/{id}", response_model=schemas.Plate)
async def read_plate(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
) -> Any:
    """
    Get plate by ID.
    """
    plate = await crud.plate.get(db=db, id=id)
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    plate.fancy = f"{plate.big_image_id}/{plate.lpr_id}"
    return plate


@router.delete("/{id}", response_model=schemas.Plate)
def delete_plate(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
) -> Any:
    """
    Delete a plate.
    """
    plate = crud.plate.get(db=db, id=id)
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    plate = crud.plate.remove(db=db, id=id)
    return plate


@router.get("/findplates/", response_model=schemas.GetPlates)
async def findplates(
    db: AsyncSession = Depends(deps.get_db_async),
    input_ocr: str = None,
    input_camera_code: str = None,
    input_owner_id: int = None,
    input_time_min: datetime = None,
    input_time_max: datetime = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve records.
    """

    plates = await crud.plate.find_plates(
        db,
        input_ocr=input_ocr,
        input_camera_code=input_camera_code,
        input_owner_id=input_owner_id,
        input_time_min=input_time_min,
        input_time_max=input_time_max,
        skip=skip,
        limit=limit,
    )
    for i in range(len(plates)):
        plates[i].fancy = f"{plates[i].big_image_id}/{plates[i].lpr_id}"

    return schemas.GetPlates(items=plates, all_items_count=len(plates))


@router.get("/random_plate/{camera_id}", response_model=schemas.Plate)
async def get_random_plate_by_camera_id_(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    camera_id: int,
) -> Any:
    """
    Get plate by camera_id.
    """
    plate = await crud.plate.get_random_plate_by_camera_id(
        db=db, camera_id=camera_id
    )
    if not plate:
        raise HTTPException(status_code=404, detail="Plate not found")
    plate.fancy = f"{plate.big_image_id}/{plate.lpr_id}"
    return plate
