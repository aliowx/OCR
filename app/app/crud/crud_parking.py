import logging
from typing import Awaitable, List, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.db.base_class import Base
from app.models.parking import Parking
from app.schemas.parking import ParkingCreate, ParkingUpdate

ModelType = TypeVar("ModelType", bound=Base)

logger = logging.getLogger(__name__)


class CRUDparking(CRUDBase[Parking, ParkingCreate, ParkingUpdate]):

    async def find_lines_camera(
        self,
        db: Session | AsyncSession,
        *,
        input_camera_id: int = None,
        input_number_line: int = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Parking] | Awaitable[List[Parking]]:

        query = select(Parking)

        filters = [Parking.is_deleted == False]

        if input_camera_id:
            filters.append(Parking.camera_id == input_camera_id)

        if input_number_line:
            filters.append(Parking.number_line == input_number_line)

        if limit is None:
            return self._all(db.scalars(query.offset(skip)))

        return await self._all(
            db.scalars(query.filter(*filters).offset(skip).limit(limit))
        )

    async def one_parking(
        self,
        db: Session | AsyncSession,
        *,
        input_camera_id: int = None,
        input_number_line: int = None,
    ) -> Parking | Awaitable[Parking]:

        query = select(Parking)

        filters = [Parking.is_deleted == False]

        if input_camera_id is not None:
            filters.append(Parking.camera_id == input_camera_id)

        if input_number_line is not None:
            filters.append(Parking.number_line == input_number_line)

        return await self._first(db.scalars(query.filter(*filters)))


parking = CRUDparking(Parking)
