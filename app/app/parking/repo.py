import logging
from typing import Awaitable, List, TypeVar

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.db.base_class import Base

from .models import Camera, Parking, ParkingLot, ParkingZone
from .schemas.camera import CameraCreate, CameraUpdate
from .schemas.parking import ParkingCreate, ParkingUpdate
from .schemas.parkinglot import ParkingLotCreate, ParkingLotUpdate
from .schemas.parkingzone import ParkingZoneCreate, ParkingZoneUpdate

ModelType = TypeVar("ModelType", bound=Base)

logger = logging.getLogger(__name__)


class ParkingLotRepository(
    CRUDBase[ParkingLot, ParkingLotCreate, ParkingLotUpdate]
):

    async def find_lines_camera(
        self,
        db: Session | AsyncSession,
        *,
        input_camera_id: int = None,
        input_number_line: int = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ParkingLot] | Awaitable[List[ParkingLot]]:

        query = select(ParkingLot)

        filters = [ParkingLot.is_deleted == False]

        if input_camera_id:
            filters.append(ParkingLot.camera_id == input_camera_id)

        if input_number_line:
            filters.append(ParkingLot.number_line == input_number_line)

        if limit is None:
            return self._all(db.scalars(query.offset(skip)))

        return await self._all(
            db.scalars(query.filter(*filters).offset(skip).limit(limit))
        )

    async def one_parkinglot(
        self,
        db: Session | AsyncSession,
        *,
        input_camera_id: int = None,
        input_number_line: int = None,
    ) -> ParkingLot | Awaitable[ParkingLot]:

        query = select(ParkingLot)

        filters = [ParkingLot.is_deleted == False]

        if input_camera_id is not None:
            filters.append(ParkingLot.camera_id == input_camera_id)

        if input_number_line is not None:
            filters.append(ParkingLot.number_line == input_number_line)

        return await self._first(db.scalars(query.filter(*filters)))


class CameraRepository(CRUDBase[Camera, CameraCreate, CameraUpdate]):

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


class ParkingRepository(CRUDBase[Parking, ParkingCreate, ParkingUpdate]):
    async def get_main_parking(self, db: AsyncSession) -> Parking | None:
        parkings = await self.get_multi(db)
        if not parkings:
            return None
        return parkings[0]


class ParkingZoneRepository(
    CRUDBase[ParkingZone, ParkingZoneCreate, ParkingZoneUpdate]
):
    async def get_by_name(
        self, db: AsyncSession, name: str
    ) -> ParkingZone | None:
        zone = await self._first(
            db.scalars(
                select(self.model).filter(
                    func.lower(self.model.name) == name.lower(),
                    self.model.is_deleted == False,
                )
            )
        )
        return zone


parkinglot = ParkingLotRepository(ParkingLot)
camera = CameraRepository(Camera)
parking = ParkingRepository(Parking)
parkingzone = ParkingZoneRepository(ParkingZone)
