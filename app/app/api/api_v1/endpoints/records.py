import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, models, schemas, utils
from app.api import deps
from app.utils import APIResponse, APIResponseType
from app import exceptions as exc
from app.api.api_v1.services import records_services

logger = logging.getLogger(__name__)
namespace = "records"
router = APIRouter()


@router.get("/")
async def read_records(
    db: AsyncSession = Depends(deps.get_db_async),
    score: float = 0,
    skip: int = 0,
    limit: int = 100,
    asc: bool = False,
) -> APIResponseType[schemas.GetRecords]:
    """
    All record
    """

    records = await records_services.calculator_price(
        db, score=score, skip=skip, limit=limit, asc=asc
    )

    return APIResponse(records)


@router.post("/")
async def create_record(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    record_in: schemas.RecordCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.RecordCreate]:
    """
    Create new item.
    """
    record = await crud.record.create(db=db, obj_in=record_in)
    return APIResponse(record)


@router.get("/{id}")
async def read_record(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    id: int,
) -> APIResponseType[schemas.Record]:
    """
    Get record by ID.
    """
    record = await crud.record.get(db=db, id=id)
    if not record:
        exc.ServiceFailure(
            detail="Record Not Found", msg_code=utils.MessageCodes.not_found
        )
    return APIResponse(record)


@router.get("/find/search")
async def findrecords(
    db: AsyncSession = Depends(deps.get_db_async),
    input_ocr: str = None,
    input_start_time_min: datetime = None,
    input_start_time_max: datetime = None,
    input_end_time_min: datetime = None,
    input_end_time_max: datetime = None,
    input_score: float = None,
    skip: int = 0,
    limit: int = 100,
) -> APIResponseType[schemas.GetRecords]:
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
        skip=skip,
        limit=limit,
    )

    return APIResponse(
        schemas.GetRecords(items=records[0], all_items_count=records[1])
    )
