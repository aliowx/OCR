import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.api import deps
from app.parking.repo import parking_repo
from app.parking.schemas import parking as schemas
from app.utils import APIResponse, APIResponseType
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated


router = APIRouter()
namespace = "parkings"
logger = logging.getLogger(__name__)


@router.get("/main")
async def read_main_parking(
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
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.Parking | schemas.ParkingBase]:
    """
    Read main parking.

    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]

    """
    main_parking = await parking_repo.get_main_parking(db)
    if not main_parking:
        return APIResponse(schemas.ParkingBase(beneficiary_data=schemas.Beneficiary()))
    return APIResponse(main_parking)


@router.post("/main")
async def create_main_parking(
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
    parking_in: schemas.ParkingCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
    """
    Create main parking.

    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
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
