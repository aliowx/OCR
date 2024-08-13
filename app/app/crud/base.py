from asyncio import iscoroutine
from datetime import datetime
from typing import Any, Awaitable, Generic, Type, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model

    async def _commit_refresh_async(
        self, db: AsyncSession, db_obj: ModelType, commit: bool = True
    ) -> ModelType:
        if commit:
            await db.commit()
            await db.refresh(db_obj)
        else:
            await db.flush()
        return db_obj

    def _commit_refresh(
        self,
        db: Session | AsyncSession,
        db_obj: ModelType,
        commit: bool = True,
    ) -> ModelType | Awaitable[ModelType]:
        if isinstance(db, AsyncSession):
            return self._commit_refresh_async(db, db_obj=db_obj, commit=commit)
        if commit:
            db.commit()
            db.refresh(db_obj)
        else:
            db.flush()
        return db_obj

    async def _commit_refresh_all_async(
        self, db: AsyncSession, db_objs: list[ModelType]
    ) -> list[ModelType]:
        await db.commit()
        for db_obj in db_objs:
            await db.refresh(db_obj)
        return db_objs

    def _commit_refresh_all(
        self, db: Session | AsyncSession, db_objs: list[ModelType]
    ) -> list[ModelType] | Awaitable[list[ModelType]]:
        if isinstance(db, AsyncSession):
            return self._commit_refresh_async(db, db_obj=db_objs)
        db.commit()
        for db_obj in db_objs:
            db.refresh(db_obj)
        return db_objs

    async def _first_async(self, scalars) -> ModelType | None:
        results = await scalars
        return results.first()

    def _first(
        self, scalars
    ) -> ModelType | None | Awaitable[ModelType | None]:
        if iscoroutine(scalars):
            return self._first_async(scalars)
        return scalars.first()

    async def _last_async(self, scalars) -> ModelType | None:
        results = await scalars
        return results.last()

    def _last(self, scalars) -> ModelType | None | Awaitable[ModelType | None]:
        if iscoroutine(scalars):
            return self._last_async(scalars)
        return scalars.last()

    async def _all_async(self, scalars) -> list[ModelType]:
        results = await scalars
        return results.all()

    def _all(self, scalars) -> list[ModelType] | Awaitable[list[ModelType]]:
        if iscoroutine(scalars):
            return self._all_async(scalars)
        return scalars.all()

    def get(
        self, db: Session | AsyncSession, id: Any
    ) -> ModelType | Awaitable[ModelType] | None:
        query = select(self.model).filter(
            self.model.id == id, self.model.is_deleted == False
        )

        return self._first(db.scalars(query))

    def get_multi(
        self,
        db: Session | AsyncSession,
        *,
        skip: int = 0,
        limit: int | None = 100
    ) -> list[ModelType] | Awaitable[list[ModelType]]:
        query = (
            select(self.model)
            .filter(self.model.is_deleted == False)
            .offset(skip)
        )
        if limit is None:
            return self._all(db.scalars(query))
        return self._all(db.scalars(query.limit(limit)))

    def get_multi_ordered(
        self,
        db: Session | AsyncSession,
        *,
        skip: int = 0,
        limit: int | None = 100,
        asc: bool = False
    ) -> list[ModelType] | Awaitable[list[ModelType]]:
        query = (
            select(self.model)
            .filter(self.model.is_deleted == False)
            .order_by(self.model.id.asc() if asc else self.model.id.desc())
            .offset(skip)
        )
        if limit is None:
            return self._all(db.scalars(query))
        return self._all(db.scalars(query.limit(limit)))

    def create(
        self,
        db: Session | AsyncSession,
        *,
        obj_in: CreateSchemaType | dict,
        commit: bool = True
    ) -> ModelType | Awaitable[ModelType]:
        # asyncpg raises DataError for str datetime fields
        # jsonable_encoder converts datetime fields to str
        # to avoid asyncpg error pass obj_in data as a dict
        # with datetime fields with python datetime type
        obj_in_data = obj_in
        if not isinstance(obj_in, dict):
            obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        return self._commit_refresh(db=db, db_obj=db_obj, commit=commit)

    def update(
        self,
        db: Session | AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any] | None = None,
        commit: bool = True
    ) -> ModelType | Awaitable[ModelType]:
        if obj_in is not None:
            obj_data = jsonable_encoder(db_obj)
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(mode="json",exclude_unset=True)
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
        if hasattr(self.model, "modified"):
            setattr(db_obj, "modified", datetime.now())
        db.add(db_obj)
        return self._commit_refresh(db=db, db_obj=db_obj, commit=commit)

    def update_multi(
        self, db: Session | AsyncSession, *, db_objs: list[ModelType]
    ) -> list[ModelType] | Awaitable[list[ModelType]]:
        if hasattr(self.model, "modified"):
            for db_obj in db_objs:
                setattr(db_obj, "modified", datetime.now())
        db.add_all(db_objs)
        return self._commit_refresh_all(db=db, db_objs=db_objs)

    def count(self, db: Session | AsyncSession) -> int | Awaitable[int]:
        q = (
            select(self.model)
            .with_only_columns(func.count())
            .filter(self.model.is_deleted == False)
        )
        return db.scalar(q)

    def remove(
        self, db: Session | AsyncSession, *, id: int, commit: bool = True
    ) -> ModelType:
        if isinstance(db, AsyncSession):
            return self._remove_async(db, id=id, commit=commit)
        obj = db.query(self.model).get(id)
        return self.update(
            db=db, db_obj=obj, obj_in={"is_deleted": True}, commit=commit
        )

    async def _remove_async(
        self, db: AsyncSession, *, id: int, commit: bool = True
    ) -> ModelType:
        obj = await self.get(db, id=id)
        return await self.update(
            db=db, db_obj=obj, obj_in={"is_deleted": True}, commit=commit
        )

    async def count_by_filter(
        self, db: Session | AsyncSession, *, filters: list
    ) -> int | Awaitable[int]:
        q = select(self.model).with_only_columns(func.count()).filter(*filters)
        return await db.scalar(q)
