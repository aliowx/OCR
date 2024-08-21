import logging
from typing import Any

from fastapi import APIRouter, Depends,WebSocket
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from cache.redis import redis_connect_async

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
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated


router = APIRouter()
namespace = "plates"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_plates(
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
    params: schemas.ParamsPlates = Depends(),
) -> APIResponseType[PaginatedContent[list[schemas.Plate]]]:
    """
    All plates.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
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



@router.websocket("/plates")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection = await redis_connect_async(240)  # 3 mins
    async with connection.pubsub() as channel:
        await channel.subscribe("plates:1")
        try:
            while True:
                data = await channel.get_message(
                    ignore_subscribe_messages=True, timeout=240
                )
                if data and "data" in data:
                    print(data["data"])
                    await websocket.send_text(data["data"])
        finally:
            channel.unsubscribe("plates:1")


@router.post("/")
async def create_plate(
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
    plate_in: schemas.PlateCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
    """
    Create new item.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    result = celery_app.send_task(
        "add_plates",
        args=[jsonable_encoder(plate_in)],
    )

    return APIResponse(f"This id task => {result.task_id}")


@router.get("/{id}")
async def read_plate(
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
) -> APIResponseType[schemas.Plate]:
    """
    Get plate by ID.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    plate = await crud.plate.get(db=db, id=id)
    if not plate:
        raise exc.ServiceFailure(
            detail="not exist.",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(plate)
