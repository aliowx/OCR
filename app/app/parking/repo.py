import logging
from typing import Awaitable, List, TypeVar

from sqlalchemy import exists, false, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.db.base_class import Base

from .models import (
    Camera,
    Equipment,
    Parking,
    ParkingLot,
    ParkingZone,
    ParkingZonePrice,
    PlateRule,
    Rule,
    ZoneRule,
)
from .schemas.camera import CameraCreate, CameraUpdate
from .schemas.equipment import (
    EquipmentCreate,
    EquipmentUpdate,
    ReadEquipmentsFilter,
)
from .schemas.parking import ParkingCreate, ParkingUpdate
from .schemas.parkinglot import ParkingLotCreate, ParkingLotUpdate
from .schemas.parkingzone import (
    ParkingZoneCreate,
    ParkingZonePriceCreate,
    ParkingZonePriceUpdate,
    ParkingZoneUpdate,
)
from .schemas.rule import (
    PlateRuleCreate,
    ReadRulesFilter,
    RuleCreate,
    ZoneRuleCreate,
)

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

        filters = [ParkingLot.is_deleted == false()]

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

        filters = [ParkingLot.is_deleted == false()]

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

        filters = [Camera.is_deleted == false()]

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

        filters = [Camera.is_deleted == false()]

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
                    self.model.is_deleted == false(),
                )
            )
        )
        return zone


class EquipmentRepository(
    CRUDBase[Equipment, EquipmentCreate, EquipmentUpdate]
):
    def _build_filters(self, filters: ReadEquipmentsFilter) -> list:
        orm_filters = []
        if filters.parking_id__eq:
            orm_filters.append(self.model.parking_id == filters.parking_id__eq)
        if filters.zone_id__eq:
            orm_filters.append(self.model.zone_id == filters.zone_id__eq)
        if filters.equipment_type__eq:
            orm_filters.append(
                self.model.equipment_type == filters.equipment_type__eq
            )
        if filters.equipment_status__eq:
            orm_filters.append(
                self.model.equipment_status == filters.equipment_status__eq
            )
        if filters.ip_address__eq:
            orm_filters.append(self.model.ip_address == filters.ip_address__eq)
        if filters.serial_number__eq:
            orm_filters.append(
                self.model.serial_number == filters.serial_number__eq
            )
        return orm_filters

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filters: ReadEquipmentsFilter,
        asc: bool = False,
    ) -> tuple[list[Equipment], int]:
        orm_filters = self._build_filters(filters)
        query = select(Equipment).filter(
            self.model.is_deleted == false(),
            *orm_filters,
        )

        q = query.with_only_columns(func.count())
        total_count = db.scalar(q)

        order_by = self.model.id.asc() if asc else self.model.id.desc()
        query = query.order_by(order_by)

        if filters.limit is None:
            return (
                await self._all(db.scalars(query.offset(filters.skip))),
                await total_count,
            )
        return (
            await self._all(
                db.scalars(query.offset(filters.skip).limit(filters.limit))
            ),
            await total_count,
        )


class ParkingZonePriceRepository(
    CRUDBase[ParkingZonePrice, ParkingZonePriceCreate, ParkingZonePriceUpdate]
):
    async def pricing_exists(
        self, db: AsyncSession, zone_id: int, price_id: int, priority: int
    ) -> bool:
        result = await db.execute(
            select(
                exists().where(
                    self.model.zone_id == zone_id,
                    self.model.price_id == price_id,
                    self.model.priority == priority,
                    self.model.is_deleted == false(),
                )
            )
        )
        return result.scalar()


class RuleRepository(CRUDBase[Rule, RuleCreate, None]):
    def update(self, *args, **kwargs) -> None:
        raise NotImplementedError

    def _build_filters(self, filters: ReadRulesFilter) -> list:
        orm_filters = []
        if filters.name_fa__eq:
            orm_filters.append(self.model.name_fa == filters.name_fa__eq)
        if filters.name_fa__contains:
            orm_filters.append(
                self.model.name_fa.contains(filters.name_fa__contains)
            )
        if filters.rule_type__eq:
            orm_filters.append(self.model.rule_type == filters.rule_type__eq)
        if filters.start_datetime__gte:
            orm_filters.append(
                self.model.start_datetime >= filters.start_datetime__gte
            )
        if filters.start_datetime__lte:
            orm_filters.append(
                self.model.start_datetime <= filters.start_datetime__lte
            )
        if filters.end_datetime__gte:
            orm_filters.append(
                self.model.end_datetime >= filters.end_datetime__gte
            )
        if filters.end_datetime__lte:
            orm_filters.append(
                self.model.end_datetime <= filters.end_datetime__lte
            )
        if filters.registeration_date__gte:
            orm_filters.append(
                self.model.registeration_date
                >= filters.registeration_date__gte
            )
        if filters.registeration_date__lte:
            orm_filters.append(
                self.model.registeration_date
                <= filters.registeration_date__lte
            )

        return orm_filters

    async def get_multi_with_filters(
        self,
        db: AsyncSession,
        *,
        filters: ReadRulesFilter,
        asc: bool = False,
    ) -> tuple[list[Rule], int]:
        orm_filters = self._build_filters(filters)
        query = select(Rule).filter(
            self.model.is_deleted == false(),
            *orm_filters,
        )

        q = query.with_only_columns(func.count())
        total_count = db.scalar(q)

        order_by = self.model.id.asc() if asc else self.model.id.desc()
        query = query.order_by(order_by)

        if filters.limit is None:
            return (
                await self._all(db.scalars(query.offset(filters.skip))),
                await total_count,
            )
        return (
            await self._all(
                db.scalars(query.offset(filters.skip).limit(filters.limit))
            ),
            await total_count,
        )


class ZoneRuleRepository(CRUDBase[ZoneRule, ZoneRuleCreate, None]):
    def updates(self, *args, **kwargs) -> None:
        raise NotImplementedError

    async def find(
        self, db: AsyncSession, rule_id: int, zone_id: int
    ) -> Rule | None:
        rule = await self._first(
            db.scalars(
                select(self.model).filter(
                    self.model.rule_id == rule_id,
                    self.model.zone_id == zone_id,
                    self.model.is_deleted == false(),
                )
            )
        )
        return rule


class PlateRuleRepository(CRUDBase[PlateRule, PlateRuleCreate, None]):
    def update(self, *args, **kwargs) -> None:
        raise NotImplementedError

    async def find(
        self, db: AsyncSession, rule_id: int, plate: str
    ) -> PlateRule | None:
        rule = await self._first(
            db.scalars(
                select(self.model).filter(
                    self.model.rule_id == rule_id,
                    self.model.plate == plate,
                    self.model.is_deleted == false(),
                )
            )
        )
        return rule


parkinglot_repo = ParkingLotRepository(ParkingLot)
camera_repo = CameraRepository(Camera)
parking_repo = ParkingRepository(Parking)
parkingzone_repo = ParkingZoneRepository(ParkingZone)
equipment_repo = EquipmentRepository(Equipment)
parkingzoneprice_repo = ParkingZonePriceRepository(ParkingZonePrice)
rule_repo = RuleRepository(Rule)
zonerule_repo = ZoneRuleRepository(ZoneRule)
platerule_repo = PlateRuleRepository(PlateRule)
