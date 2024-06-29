import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas, utils
from app.api import deps
from app.api.services import records_services
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType

logger = logging.getLogger(__name__)
namespace = "records"
router = APIRouter()


@router.get("/")
async def read_records(
    db: AsyncSession = Depends(deps.get_db_async),
    record_in: schemas.ParamsRecord = Depends(),
    asc: bool = False,
) -> APIResponseType[schemas.GetRecords]:
    """
    All record
    """

    records = await records_services.calculator_price(
        db, params=record_in
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


