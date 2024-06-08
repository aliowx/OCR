import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.api import deps
from app.core import exceptions as exc
from app.parking.repo import parking_repo
from app.parking.schemas import parking as schemas
from app.utils import APIResponse, APIResponseType, MessageCodes

router = APIRouter()
namespace = "parkings"
logger = logging.getLogger(__name__)


@router.get("/main")
async def read_main_parking(
    db: AsyncSession = Depends(deps.get_db_async),
    skip: int = 0,
    limit: int = 100,
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Parking | None]:
    """
    Read main parking.
    """
    main_parking = await parking_repo.get_main_parking(db)
    if not main_parking:
        raise exc.ServiceFailure(
            detail="Parking not found.",
            msg_code=MessageCodes.not_found,
        )
    return APIResponse(main_parking)


@router.post("/main")
async def create_main_parking(
    *,
    db: AsyncSession = Depends(deps.get_db_async),
    parking_in: schemas.ParkingCreate,
    _: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[Any]:
    """
    Create main parking.
    """
    # FIXME: add input validations
    main_parking = await parking_repo.get_main_parking(db)
    if not main_parking:
        main_parking = await parking_repo.create(db, obj_in=parking_in)
    else:
        beneficiary_data = main_parking.beneficiary_data.copy()
        beneficiary_data.update(
            parking_in.beneficiary_data.model_dump(exclude_none=True)
        )
        main_parking.beneficiary_data = beneficiary_data
        main_parking_update_data = parking_in.model_dump(exclude_none=True)
        main_parking_update_data.pop("beneficiary_data", None)
        main_parking = await parking_repo.update(
            db, db_obj=main_parking, obj_in=main_parking_update_data
        )
    return APIResponse(main_parking)
