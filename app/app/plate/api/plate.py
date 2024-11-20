import logging
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, utils
from app.plate import schemas
from app.plate.repo import plate_repo, auth_otp_repo
from app.api import deps
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType, PaginatedContent
from app.plate.services import plate as ServicePlate
from collections import Counter
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated, Any
from random import randint
import requests
from datetime import datetime, UTC, timedelta
from app.core.config import settings
from cache.redis import redis_connect_async

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


@router.get("/list-action")
async def list_action(
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
) -> APIResponseType[list[str]]:
    """
    Retrieve plate.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    plate_types = [ptype.value for ptype in schemas.PlateType]
    return APIResponse(plate_types)


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
    plates_in: list[schemas.PlateCreate],
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[Any]:
    """
    Create new plate.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    list_plate = [plate.plate for plate in plates_in]
    # Count occurrences of each plate number
    plate_counts = Counter(list_plate)

    # Find and print duplicate plates
    duplicates = {plate for plate, count in plate_counts.items() if count > 1}

    list_duplicate = [plates_duplicates for plates_duplicates in duplicates]

    new_plates_in = [
        plate for plate in plates_in if plate.plate not in duplicates
    ]

    plates_exist = await plate_repo.get_multi_by_plate(
        db=db,
        plate=[plate.plate for plate in new_plates_in],
        type_list=plates_in[0].type.value,
    )

    pop_plates = set(
        plate for plate in plates_exist
    )  # Convert to set for faster lookup

    # Filter out plates that already exist in the database
    new_plates = [
        plate.model_dump()
        for plate in new_plates_in
        if plate.plate not in pop_plates
    ]
    plate = await plate_repo.create_multi(db, objs_in=new_plates)
    return APIResponse(
        [
            {
                "new": plate,
                "exists": pop_plates,
                "duplicates": list(list_duplicate),
            }
        ]
    )


@router.post("/upload-excel")
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
    type_list: schemas.PlateType = Query(...),
    file: UploadFile = File(...),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[Any]:
    """
    Create new plate.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    plates = await ServicePlate.create_multi_by_excel(
        db, file=file, type_list=type_list
    )

    return APIResponse(plates)


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


@router.post("/sending-otp-code")
async def create_Plate(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.APPS,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    params: schemas.PlateCreateOTP,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[Any]:
    """
    Create new plate.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    plate_validate = models.base.validate_iran_plate(params.plate)
    phone_number_validate = models.base.validate_iran_phone_number(
        params.phone_number
    )

    redis_client = await redis_connect_async()

    check_no_spam = await redis_client.get(params.phone_number)
    if check_no_spam:
        raise exc.ServiceFailure(
            detail=f"after {await redis_client.ttl(params.phone_number)} seconds try agin",
            msg_code=utils.MessageCodes.try_after,
        )
    await redis_client.set(params.phone_number, params.plate, ex=120)
    gen_code = randint(10000, 99999)

    create_otp = await auth_otp_repo.create(
        db,
        obj_in=schemas.AuthOTPCreate(
            phone_number=params.phone_number,
            code=gen_code,
            expire_at=datetime.now(UTC).replace(tzinfo=None),
            is_used=False,
        ).model_dump(),
    )

    params_sending_code = {
        "phoneNumber": params.phone_number,
        "textMessage": f"بازار بزرگ ایران (ایران مال) \n کد تایید شما : {gen_code}",
    }
    send_code = requests.post(
        settings.URL_SEND_SMS,
        params=params_sending_code,
    )

    return APIResponse({"data": "sending code"})


@router.post("/create-plate-with-code-otp")
async def create_plate(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.APPS,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    *,
    code_in: int,
    params: schemas.PlateCreateOTP,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[Any]:
    """
    Create new plate.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    plate_validate = models.base.validate_iran_plate(params.plate)
    phone_number_validate = models.base.validate_iran_phone_number(
        params.phone_number
    )

    redis_client = await redis_connect_async()
    await redis_client.rpush(params.phone_number, code_in)
    if await redis_client.ttl(params.phone_number) == -1:
        await redis_client.expire(params.phone_number, 300)
    get_keys_count = await redis_client.llen(params.phone_number)
    if get_keys_count > 2:
        time_expire = await redis_client.ttl(params.phone_number)
        raise exc.ServiceFailure(
            detail=f"try after {time_expire} seconds",
            msg_code=utils.MessageCodes.try_after,
        )

    cheking_code = await auth_otp_repo.chking_code(
        db, code_in=code_in, phone_number_in=params.phone_number
    )

    if not cheking_code:
        raise exc.ServiceFailure(
            detail="code not found",
            msg_code=utils.MessageCodes.not_found,
        )
    if cheking_code.expire_at + timedelta(minutes=2) < datetime.now(
        UTC
    ).replace(tzinfo=None):
        cheking_code.is_used = True
        update_otp = await auth_otp_repo.update(db, db_obj=cheking_code)
        raise exc.ServiceFailure(
            detail="expire code",
            msg_code=utils.MessageCodes.not_found,
        )

    cheking_code.is_used = True
    update_otp = await auth_otp_repo.update(db, db_obj=cheking_code)

    plates_exist = await plate_repo.get_plate(
        db=db,
        type_list=schemas.plate.PlateType.phone,
        plate=params.plate,
    )

    if plates_exist is None:
        create_plate = await plate_repo.create(
            db,
            obj_in=schemas.PlateCreateOTP(
                plate=params.plate,
                type=schemas.PlateType.phone,
                phone_number=params.phone_number,
            ),
        )
    if (
        plates_exist is not None
        and plates_exist.phone_number != params.phone_number
    ):
        plates_exist.phone_number = params.phone_number
        create_plate = await plate_repo.update(db, db_obj=plates_exist)

    return APIResponse({"data": "save phone number in system"})
