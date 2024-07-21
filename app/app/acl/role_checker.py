from typing import Annotated

from fastapi import Depends

from app.core import exceptions as exc
from app.acl.role import UserRoles
from app.api import deps
from app.users.models import User
from app.utils.message_codes import MessageCodes

ALL_ROLES = [
    UserRoles.SUPERADMIN,
    UserRoles.ADMIN_EQUIPMENT,
    UserRoles.ADMIN_PRICE,
    UserRoles.ADMIN_PLATE_RECORD,
    UserRoles.ADMIN_USER,
    UserRoles.ADMIN_ZONE_SPOT,
    UserRoles.READER_EQUIPMENT,
    UserRoles.READER_PLATE_RECORD,
    UserRoles.READER_PRICE,
    UserRoles.READER_USER,
    UserRoles.READER_ZONE_SPOT,
]
ADMIN_READER_EQUIPMENT_ROLES = [
    UserRoles.ADMIN_EQUIPMENT,
    UserRoles.READER_EQUIPMENT,
]
READER_USER = [UserRoles.READER_USER]


class RoleChecker:
    def __init__(self, allowed_roles: list[UserRoles]):
        self.allowed_roles = allowed_roles

    def __call__(
        self, user: Annotated[User, Depends(deps.get_current_active_user)]
    ):
        if user.role in self.allowed_roles:
            return True
        raise exc.ServiceFailure(
            detail="You do not have permission to perform this operation",
            msg_code=MessageCodes.not_permission,
        )
