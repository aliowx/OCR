import time
from datetime import datetime, timedelta
from typing import Any, List

# import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.api import deps
from cache.redis import redis_client
from app.core.celery_app import celery_app
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


router = APIRouter()


@router.get("/", response_model=schemas.GetRecords)
async def read_records(
    db: AsyncSession = Depends(deps.get_db_async),
    score: float = 0,
    skip: int = 0,
    limit: int = 100,
    asc: bool = False,
    by_id: bool = False,
) -> Any:
    """
    Retrieve plates.
    """
    if by_id:
        records = await crud.record.get_multi_by_id(
            db, skip=skip, limit=limit, asc=asc
        )
    else:
        # records = await crud.record.get_multi(db, skip=skip, limit=limit, asc=asc)
        records = await crud.record.get_multi_filter(
            db, score=score, skip=skip, limit=limit, asc=asc
        )
    for i in range(len(records)):
        records[i].fancy = (
            f"{records[i].best_big_image_id}/{records[i].best_lpr_id}"
        )
    # all_items_count = crud.record.get_count(db)
    # all_items_count = redis_client.get("records_count")
    return schemas.GetRecords(items=records, all_items_count=len(records))


@router.get("/firstrecords/", response_model=List[schemas.Record])
async def read_records_firstrecords(
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve records.
    """
    records = await crud.record.get_multi_filter(
        db, record_number=0, skip=skip, limit=limit
    )
    for i in range(len(records)):
        records[i].fancy = (
            f"{records[i].best_big_image_id}/{records[i].best_lpr_id}"
        )
    return records


@router.get("/checkoperatory/", response_model=list[schemas.Record])
async def read_records_checkoperatory(
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve unchecked records.
    """
    records = await crud.record.get_multi_filter(
        db, ocr_checked=False, skip=skip, limit=limit
    )
    for i in range(len(records)):
        records[i].fancy = (
            f"{records[i].best_big_image_id}/{records[i].best_lpr_id}"
        )
    return records


@router.post("/", response_model=schemas.Record)
async def create_record(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    record_in: schemas.RecordCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new item.
    """
    current_user_dict = jsonable_encoder(current_user)
    # # TODO: this method count on the send time not the record time this must be changed for async systems
    # key = f"{record_in.ocr}:{current_user.id}"
    # record_number = redis_client.get(key)
    # if record_number is None:
    #     record_in.record_number = 0
    # else:
    #     record_in.record_number = int(record_number) + 1
    # logger.info(f"record's record number: {record_in.record_number}")
    # redis_client.setex(key, timedelta(seconds=settings.FREE_TIME_BETWEEN_RECORDS), int(record_in.record_number))

    # logger.info(f"create record current_user: {current_user_dict}")
    record = await crud.record.create_with_owner(
        db=db, obj_in=record_in, owner_id=current_user.id
    )
    record.fancy = f"{record.best_big_image_id}/{record.best_lpr_id}"
    if settings.CPAYTAX_USERNAME is not None and record.record_number == 0:
        celery_app.send_task(
            "app.worker.send_plate",
            args=[jsonable_encoder(record), current_user_dict],
        )
    return record


@router.put("/{id}", response_model=schemas.Record)
async def update_record(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
    record_in: schemas.RecordUpdate,
) -> Any:
    """
    Update a Record.
    """
    record = await crud.record.get(db=db, id=id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    record = await crud.record.update(db=db, db_obj=record, obj_in=record_in)
    return record


# @router.put("/chechoperatory/{id}", response_model=schemas.Record)
# async def update_plate_ocrchecked(
#     *,
#     db: AsyncSession = Depends(deps.get_db_async),
#     id: int,
#     record_in: schemas.RecordUpdateCheckOperatory,
# ) -> Any:
#     """
#     Update a Record's OCR.
#     """
#     record = await crud.record.get(db=db, id=id)
#     if not record:
#         raise HTTPException(status_code=404, detail="Record not found")
#     if record.additional_data is None:
#         record.additional_data = {}
#     record.additional_data["checkoperatory"] = record_in.additional_data
#     if "checkoperatory_times" not in record.additional_data:
#         record.additional_data["checkoperatory_times"] = []
#     record.additional_data["checkoperatory_times"].append(
#         datetime.now().isoformat()
#     )
#     record_in.additional_data = record.additional_data
#     logger.info(record_in.ocr_checked)
#     logger.info(record_in.additional_data)
#     record = await crud.record.update_checkoperatory(
#         db=db, db_obj=record, obj_in=record_in
#     )
#     return record


@router.get("/{id}", response_model=schemas.Record)
async def read_record(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
) -> Any:
    """
    Get record by ID.
    """
    record = await crud.record.get(db=db, id=id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    record.fancy = f"{record.best_big_image_id}/{record.best_lpr_id}"
    return record


@router.delete("/{id}", response_model=schemas.Record)
def delete_record(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
) -> Any:
    """
    Delete a record.
    """
    record = crud.record.get(db=db, id=id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    record = crud.record.remove(db=db, id=id)
    return record


@router.get("/findrecords/", response_model=schemas.GetRecords)
async def findrecords(
    db: AsyncSession = Depends(deps.get_db_async),
    input_ocr: str = None,
    input_start_time_min: datetime = None,
    input_start_time_max: datetime = None,
    input_end_time_min: datetime = None,
    input_end_time_max: datetime = None,
    input_score: float = None,
    input_gateway_name: int = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve records.
    """
    records = await crud.record.find_records(
        db,
        input_ocr=input_ocr,
        input_start_time_min=input_start_time_min,
        input_start_time_max=input_start_time_max,
        input_end_time_min=input_end_time_min,
        input_end_time_max=input_end_time_max,
        input_score=input_score,
        input_gateway_name=input_gateway_name,
        skip=skip,
        limit=limit,
    )
    for i in range(len(records)):
        records[i].fancy = (
            f"{records[i].best_big_image_id}/{records[i].best_lpr_id}"
        )

    return schemas.GetRecords(items=records, all_items_count=len(records))
