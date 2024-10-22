import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app import models, utils
from app.ticket import schemas
from app.ticket.repo import ticket_repo
from app.api import deps
from app.core import exceptions as exc
from app.utils import APIResponse, APIResponseType, PaginatedContent

from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated

router = APIRouter()
namespace = "ticket"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_ticket(
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
    params: schemas.ParamsTicket = Depends(),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[PaginatedContent[list[schemas.Ticket]]]:
    """
    Retrieve ticket.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    ticket, total_count = await ticket_repo.get_multi_by_filter(
        db, params=params
    )
    return APIResponse(
        PaginatedContent(
            data=ticket,
            total_count=total_count,
            size=params.size,
            page=params.page,
        )
    )


@router.post("/")
async def create_ticket(
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
    ticket_in: schemas.TicketCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Ticket]:
    """
    Create new ticket.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """

    ticket = await ticket_repo.create(db, obj_in=ticket_in)
    return APIResponse(ticket)


@router.get("/{id}")
async def read_ticket_by_id(
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
) -> APIResponseType[schemas.Ticket]:
    """
    Get a specific ticket by id.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    ticket = await ticket_repo.get(db, id=id)
    if not ticket:
        raise exc.ServiceFailure(
            detail="ticket not found",
            msg_code=utils.MessageCodes.not_found,
        )
    return APIResponse(ticket)


@router.delete("/{id}")
async def delete_ticket(
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
) -> APIResponseType[schemas.Ticket]:
    """
    delete ticket.
    user access to this [ ADMINISTRATOR ]
    """
    ticket = await ticket_repo.get(db, id=id)
    if not ticket:
        raise exc.ServiceFailure(
            detail="ticket not found",
            msg_code=utils.MessageCodes.not_found,
        )
    del_ticket = await ticket_repo.remove(db, id=ticket.id, commit=True)
    return APIResponse(del_ticket)


@router.put("/{id}")
async def update_ticket(
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
    ticket_in: schemas.TicketUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> APIResponseType[schemas.Ticket]:
    """
    Update a ticket.
    user access to this [ ADMINISTRATOR , PARKING_MANAGER ]
    """
    ticket = await ticket_repo.get(db, id=id)
    if not ticket:
        raise exc.ServiceFailure(
            detail="The ticket does't exist in the system",
            msg_code=utils.MessageCodes.not_found,
        )
    ticket = await ticket_repo.update(db, db_obj=ticket, obj_in=ticket_in)
    return APIResponse(ticket)
