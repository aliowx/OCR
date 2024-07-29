import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.api import deps
from app.core.exceptions import ServiceFailure
from app.parking.repo import rule_repo
from app.parking.schemas import rule as schemas
from app.parking.services import rule as rule_services
from app.utils import (
    APIResponse,
    APIResponseType,
    MessageCodes,
    PaginatedContent,
)
from app.acl.role_checker import RoleChecker
from app.acl.role import UserRoles
from typing import Annotated

router = APIRouter()
namespace = "rules"
logger = logging.getLogger(__name__)


@router.get("/")
async def read_rules(
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.SECURITY_STAFF,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    params: schemas.ReadRulesParams = Depends(),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[PaginatedContent[list[schemas.Rule]]]:
    """
    Read rules.

    user access to this [ ADMINISTRATOR , PARKING_MANAGER , SECURITY_STAFF ]
    """
    rules = await rule_services.read_rules(db, params=params)
    return APIResponse(rules)


@router.post("/")
async def create_rule(
    *,
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.SECURITY_STAFF,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    rule_in: schemas.RuleCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.Rule]:
    """
    Create rule.

    user access to this [ ADMINISTRATOR , PARKING_MANAGER , SECURITY_STAFF ]
    """
    rule = await rule_services.create_rule(db, rule_data=rule_in)
    return APIResponse(rule)


@router.post("/zone/set")
async def set_zone_rule(
    *,
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.SECURITY_STAFF,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    rule_in: schemas.SetZoneRuleInput,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[list[schemas.ZoneRule]]:
    """
    Set zone rules.

    user access to this [ ADMINISTRATOR , PARKING_MANAGER , SECURITY_STAFF ]
    """
    rule = await rule_services.set_zone_rule(db, rules=rule_in)
    return APIResponse(rule)


@router.post("/plate/set")
async def set_plate_rule(
    *,
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.SECURITY_STAFF,
                ]
            )
        ),
    ],
    db: AsyncSession = Depends(deps.get_db_async),
    rule_in: schemas.SetPlateRuleInput,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[list[schemas.PlateRule]]:
    """
    Set plate rules.

    user access to this [ ADMINISTRATOR , PARKING_MANAGER , SECURITY_STAFF ]
    """
    rule = await rule_services.set_plate_rule(db, rules=rule_in)
    return APIResponse(rule)


@router.delete("/{rule_id}")
async def delete_rule(
    *,
    _: Annotated[
        bool,
        Depends(
            RoleChecker(
                allowed_roles=[
                    UserRoles.ADMINISTRATOR,
                    UserRoles.PARKING_MANAGER,
                    UserRoles.SECURITY_STAFF,
                ]
            )
        ),
    ],
    rule_id: int,
    db: AsyncSession = Depends(deps.get_db_async),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> APIResponseType[schemas.Rule]:
    """
    Delete rule.

    user access to this [ ADMINISTRATOR , PARKING_MANAGER , SECURITY_STAFF ]
    """
    rule = await rule_repo.get(db, id=rule_id)
    if not rule:
        raise ServiceFailure(
            detail="Rule Not Found",
            msg_code=MessageCodes.not_found,
        )
    await rule_repo.remove(db, id=rule_id)
    return APIResponse(rule)
