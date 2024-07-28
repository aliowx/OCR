from typing import Optional
from app.acl.role import UserRoles
from pydantic import BaseModel, ConfigDict


# Shared properties
class UserBase(BaseModel):
    username: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None
    role: UserRoles | None = UserRoles.PARKING_MANAGER


# Properties to receive via API on creation
class UserCreate(UserBase):
    username: str
    password: str
    role: UserRoles | None = UserRoles.PARKING_MANAGER


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# Additional properties to return via API
class User(UserInDBBase):
    pass


class ParamsUser(BaseModel):
    input_full_name: str | None = None
    input_username: str | None = None
    input_is_active: bool | None = None
    input_role: UserRoles | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
