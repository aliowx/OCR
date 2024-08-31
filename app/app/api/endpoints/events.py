import logging
from typing import Any

from fastapi import APIRouter, Depends, WebSocket
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
namespace = "events"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_events(
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
    params: schemas.ParamsEvents = Depends(),
) -> APIResponseType[PaginatedContent[list[schemas.Event]]]:
    """
    All events.
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
    events = await crud.event.find_events(db, params=params)

    return APIResponse(
        PaginatedContent(
            data=events[0],
            total_count=events[1],
            page=params.page,
            size=params.size,
        )
    )


@router.websocket("/events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection = await redis_connect_async(240)  # 3 mins
    async with connection.pubsub() as channel:
        await channel.subscribe("events:1")
        try:
            while True:
                data = await channel.get_message(
                    ignore_subscribe_messages=True, timeout=240
                )
                if data and "data" in data:
                    print(data["data"])
                    await websocket.send_text(data["data"])
        finally:
            channel.unsubscribe("events:1")


@router.post("/")
async def create_event(
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
    event_in: schemas.EventCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[Any]:
    """
    Create new item.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    result = celery_app.send_task(
        "add_events",
        args=[jsonable_encoder(event_in)],
    )

    return APIResponse(f"This id task => {result.task_id}")


@router.get("/{id}")
async def read_event(
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
) -> APIResponseType[schemas.Event]:
    """
    Get event by ID.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    event = await crud.event.get(db=db, id=id)
    if not event:
        raise exc.ServiceFailure(
            detail="not exist.",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(event)
