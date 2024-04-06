from typing import Awaitable
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.crud.base import CRUDBase
from app.models.camera import Camera
from app.schemas.camera import CameraCreate, CameraUpdate
import logging

logger = logging.getLogger(__name__)


class CRUDCamera(CRUDBase[Camera, CameraCreate, CameraUpdate]):

    async def find_cameras(
        self,
        db: Session | AsyncSession,
        *,
        input_camera_code: str = None,
        input_camera_ip: str = None,
        input_location: str = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Camera] | Awaitable[list[Camera]]:

        query = select(Camera)

        filters = [Camera.is_deleted == False]

        if input_camera_code is not None:
            filters.append(Camera.camera_code.like(f"%{input_camera_code}%"))

        if input_camera_ip is not None:
            filters.append(Camera.camera_ip.like(f"%{input_camera_ip}%"))

        if input_location is not None:
            filters.append(Camera.location.like(f"%{input_location}%"))

        if limit is None:
            return self._all(db.scalars(query.filter(*filters).offset(skip)))

        return await self._all(
            db.scalars(query.filter(*filters).offset(skip).limit(limit))
        )

    async def one_camera(
        self,
        db: Session | AsyncSession,
        *,
        input_camera_code: str = None,
    ) -> Camera | Awaitable[Camera]:

        query = select(Camera)

        filters = [Camera.is_deleted == False]

        if input_camera_code is not None:
            filters.append(Camera.camera_code.like(f"%{input_camera_code}%"))

        return await self._first(db.scalars(query.filter(*filters)))


camera = CRUDCamera(Camera)
