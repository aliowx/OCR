import logging
from typing import Awaitable, List, TypeVar

from sqlalchemy import false, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.db.base_class import Base

from .models import (
    Equipment,
    Parking,
    Spot,
    Zone,
)
from app.pricing.models import Price
from .schemas.equipment import (
    EquipmentCreate,
    EquipmentUpdate,
    FilterEquipmentsParams,
)
from .schemas.parking import ParkingCreate, ParkingUpdate
from .schemas.spot import SpotCreate, SpotUpdate
from .schemas.zone import (
    ZoneCreate,
    ZoneUpdate,
    ZonePramsFilters,
)
from app.report.schemas import ZoneReport

from app.models.base import EquipmentType

ModelType = TypeVar("ModelType", bound=Base)

logger = logging.getLogger(__name__)


class SpotRepository(CRUDBase[Spot, SpotCreate, SpotUpdate]):
    async def get_multi_with_filters(
        self,
        db: Session | AsyncSession,
        *,
        input_camera_id: int = None,
        input_number_spot: int = None,
        input_zone_id: int = None,
        skip: int = 0,
        limit: int | None = 100,
    ) -> List[Spot] | Awaitable[List[Spot]]:

        query = select(Spot)

        filters = [Spot.is_deleted == false()]

        if input_camera_id is not None:
            filters.append(Spot.camera_id == input_camera_id)

        if input_number_spot is not None:
            filters.append(Spot.number_spot == input_number_spot)

        if input_zone_id is not None:
            filters.append(Spot.zone_id == input_zone_id)

        if limit is None:
            return await self._all(
                db.scalars(query.filter(*filters).offset(skip))
            )

        return await self._all(
            db.scalars(query.filter(*filters).offset(skip).limit(limit))
        )

    async def one_spot(
        self,
        db: Session | AsyncSession,
        *,
        input_camera_id: int = None,
        input_number_spot: int = None,
    ) -> Spot | Awaitable[Spot]:

        query = select(Spot)

        filters = [Spot.is_deleted == false()]

        if input_camera_id is not None:
            filters.append(Spot.camera_id == input_camera_id)

        if input_number_spot is not None:
            filters.append(Spot.number_spot == input_number_spot)

        return await self._first(db.scalars(query.filter(*filters)))


class ParkingRepository(CRUDBase[Parking, ParkingCreate, ParkingUpdate]):
    async def get_main_parking(self, db: AsyncSession) -> Parking | None:
        parkings = await self.get_multi(db)
        if not parkings:
            return None
        return parkings[0]


class ZoneRepository(CRUDBase[Zone, ZoneCreate, ZoneUpdate]):
    async def get_by_name(
        self, db: AsyncSession, name: str, except_id: int = None
    ) -> Zone | None:

        filters = [
            func.lower(self.model.name) == name.lower(),
            self.model.is_deleted == false(),
        ]
        # find name except self for update
        if except_id is not None:
            filters.append(self.model.id != except_id)

        zone = await self._first(
            db.scalars(select(self.model).filter(*filters))
        )
        return zone

    async def get_multi_child(self, db: Session | AsyncSession, ids: int):
        if ids is not None:
            return await self._all(
                db.scalars(
                    select(Zone).filter(
                        *[Zone.parent_id.in_(ids), Zone.is_deleted == false()]
                    )
                )
            )

    async def get_zones_price(self, db: Session | AsyncSession):
        query = select(Zone.name, Price.name).join(
            Price, Zone.price_id == Price.id
        )

        zones_price = (await db.execute(query)).fetchall()

        return zones_price

    async def get_multi_ancestor(self, db: Session | AsyncSession, ids: int):
        if ids is not None:
            return await self._all(
                db.scalars(
                    select(Zone).filter(
                        *[Zone.id.in_(ids), Zone.is_deleted == false()]
                    )
                )
            )

    async def get(
        self, db: Session | AsyncSession, id: int
    ) -> ModelType | Awaitable[ModelType] | None:
        query = select(self.model).filter(
            self.model.id == id, self.model.is_deleted == False
        )

        return await self._first(db.scalars(query))

    async def get_multi_by_filter(
        self,
        db: AsyncSession,
        *,
        params: ZonePramsFilters,
    ) -> tuple[list[Zone], int]:
        query = select(Zone)

        filters = [Zone.is_deleted == false()]

        if params.input_name_zone is not None:
            filters.append(Zone.name == params.input_name_zone)

        if params.input_name_floor is not None:
            filters.append(Zone.floor_name == params.input_name_floor)

        if params.input_number_floor is not None:
            filters.append(Zone.floor_number == params.input_number_floor)

        q = query.filter(*filters).with_only_columns(func.count())
        total_count = db.scalar(q)

        order_by = Zone.id.asc() if params.asc else Zone.id.desc()

        if params.size is None:
            return (
                await self._all(
                    db.scalars(
                        query.filter(*filters)
                        .offset(params.skip)
                        .order_by(order_by)
                    )
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

    async def get_zones_by_price_id(
        self,
        db: AsyncSession,
        *,
        price_id: int,
    ) -> list[Zone]:

        return await self._all(
            db.scalars(select(Zone).filter(Zone.price_id.in_({price_id})))
        )

    async def get_price_zone_async(
        self,
        db: AsyncSession,
        *,
        zone_id: int,
    ) -> Price:

        query = select(Price).join(Zone, Zone.id == zone_id)

        filters = [Zone.is_deleted == False, Zone.price_id == Price.id]

        return await self._first(db.scalars(query.filter(*filters)))

    def get_price_zone(
        self,
        db: Session,
        *,
        zone_id: int,
    ) -> Price:

        query = select(Price).join(Zone, Zone.id == zone_id)

        filters = [Zone.is_deleted == False, Zone.price_id == Price.id]

        return self._first(db.scalars(query.filter(*filters)))

    async def get_capacity_count_zone(self, db: AsyncSession):

        query = select(func.sum(Zone.capacity), func.count(Zone.id)).filter(
            Zone.is_deleted == False
        )

        exe_fetch_query = (await db.execute(query)).fetchone()

        return exe_fetch_query


class EquipmentRepository(
    CRUDBase[Equipment, EquipmentCreate, EquipmentUpdate]
):

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        params: FilterEquipmentsParams,
    ) -> tuple[list[Equipment], int]:

        filters = [Equipment.is_deleted == false()]

        query = select(Equipment)

        if params.zone_id:
            filters.append(self.model.zone_id == params.zone_id)

        if params.equipment_type:
            filters.append(self.model.equipment_type == params.equipment_type)

        if params.equipment_status:
            filters.append(
                self.model.equipment_status == params.equipment_status
            )

        if params.ip_address:
            filters.append(self.model.ip_address == params.ip_address)

        if params.serial_number:
            filters.append(self.model.serial_number == params.serial_number)

        if params.tag:
            filters.append(self.model.tag == params.tag)

        q = query.with_only_columns(func.count()).filter(*filters)
        total_count = db.scalar(q)

        order_by = self.model.id.asc() if params.asc else self.model.id.desc()
        query = query.order_by(order_by)

        if params.size is None:
            return (
                await self._all(
                    db.scalars(query.filter(*filters).offset(params.skip))
                ),
                await total_count,
            )
        return (
            await self._all(
                db.scalars(
                    query.filter(*filters)
                    .offset(params.skip)
                    .limit(params.size)
                )
            ),
            await total_count,
        )

    async def get_entrance_exit_camera(
        self, db: AsyncSession, zone_id: int = None
    ) -> list[Equipment]:

        filters = [Equipment.is_deleted == false()]
        camera_entrance = (
            select(Equipment.tag, Zone.name)
            .filter(
                *filters,
                Equipment.equipment_type
                == EquipmentType.CAMERA_ENTRANCE_DOOR.value,
            )
            .join(Zone, Equipment.zone_id == Zone.id)
        )
        camera_exit = (
            select(Equipment.tag, Zone.name)
            .filter(
                *filters,
                Equipment.equipment_type
                == EquipmentType.CAMERA_EXIT_DOOR.value,
            )
            .join(Zone, Equipment.zone_id == Zone.id)
        )

        if zone_id is not None:
            camera_entrance = camera_entrance.filter(
                (Equipment.zone_id == zone_id)
            )
            camera_exit = camera_exit.filter((Equipment.zone_id == zone_id))

        list_camera_entrance = (await db.execute(camera_entrance)).fetchall()
        list_camera_exit = (await db.execute(camera_exit)).fetchall()
        return list_camera_entrance, list_camera_exit

    async def one_equipment(
        self, db: AsyncSession, *, serial_number: str
    ) -> Equipment:

        query = select(Equipment)

        filters = [Equipment.is_deleted == false()]

        if serial_number is not None:
            filters.append(Equipment.serial_number == serial_number)

        return await self._first(db.scalars(query.filter(*filters)))


spot_repo = SpotRepository(Spot)
parking_repo = ParkingRepository(Parking)
zone_repo = ZoneRepository(Zone)
equipment_repo = EquipmentRepository(Equipment)
