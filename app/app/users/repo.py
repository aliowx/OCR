from typing import Any, Awaitable

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase

from .models import User
from .schemas import UserCreate, UserUpdate, ParamsUser


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_username(
        self, db: Session | AsyncSession, *, username: str
    ) -> User | None | Awaitable[User | None]:
        return self._first(
            db.scalars(
                select(User).filter(
                    func.lower(User.username) == username.lower(),
                    User.is_deleted == False,
                )
            )
        )

    async def get_multi_by_filter(
        self, db: Session | AsyncSession, *, params: ParamsUser
    ) -> list[User] | Awaitable[list[User]]:

        query = select(User)

        filters = [User.is_deleted == False]

        if params.input_username is not None:
            filters.append(User.username == params.input_username)

        if params.input_full_name is not None:
            filters.append(User.full_name == params.input_full_name)

        total_count = self.count_by_filter(db, filters=filters)

        order_by = User.id.asc() if params.asc else User.id.desc()

        if params.size is None:
            return (
                await self._all(
                    db.scalars(query.filter(*filters).order_by(order_by))
                ),
                await total_count,
            )
        return (
            await self._all(
                db.scalars(
                    query.filter(*filters)
                    .offset(params.skip)
                    .limit(params.size)
                    .order_by(order_by)
                )
            ),
            await total_count,
        )

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        obj_in_data = jsonable_encoder(obj_in)
        obj_in_data["username"] = obj_in_data["username"].lower()
        obj_in_data["hashed_password"] = get_password_hash(obj_in.password)
        del obj_in_data["password"]
        obj_in_data = {k: v for k, v in obj_in_data.items() if v is not None}
        return super().create(db, obj_in=obj_in_data)

    def update(
        self,
        db: Session | AsyncSession,
        *,
        db_obj: User,
        obj_in: UserUpdate | dict[str, Any] | None = None,
    ) -> User | Awaitable[User]:
        if obj_in is None:
            return super().update(db, db_obj=db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        return super().update(db, db_obj=db_obj, obj_in=update_data)

    async def authenticate_async(
        self, db: AsyncSession, *, username: str, password: str
    ) -> User | None:
        user = await self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def authenticate(
        self, db: Session | AsyncSession, *, username: str, password: str
    ) -> User | None | Awaitable[User | None]:
        if isinstance(db, AsyncSession):
            return self.authenticate_async(
                db=db, username=username, password=password
            )
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser


user = CRUDUser(User)
