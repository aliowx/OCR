import logging
from typing import Awaitable, List, TypeVar

from sqlalchemy import exists, false, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session, selectinload

from app.crud.base import CRUDBase
from app.db.base_class import Base

from .models import (
    Equipment,
    Parking,
    Spot,
    Zone,
    ZonePrice,
    PlateRule,
    Rule,
    ZoneRule,
)
from .schemas.equipment import (
    EquipmentCreate,
    EquipmentUpdate,
    ReadEquipmentsFilter,
)
from .schemas.parking import ParkingCreate, ParkingUpdate
from .schemas.spot import SpotCreate, SpotUpdate
from .schemas.zone import (
    ZoneCreate,
    ZonePriceCreate,
    ZonePriceUpdate,
    ZoneUpdate,
    ZonePramsFilters,
)
from .schemas.rule import (
    PlateRuleCreate,
    ReadRulesFilter,
    RuleCreate,
    ZoneRuleCreate,
)

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
    async def get_by_name(self, db: AsyncSession, name: str) -> Zone | None:
        zone = await self._first(
            db.scalars(
                select(self.model).filter(
                    func.lower(self.model.name) == name.lower(),
                    self.model.is_deleted == false(),
                )
            )
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

    async def get_multi_ancesstor(self, db: Session | AsyncSession, ids: int):
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


class EquipmentRepository(
    CRUDBase[Equipment, EquipmentCreate, EquipmentUpdate]
):
    def _build_filters(self, filters: ReadEquipmentsFilter) -> list:
        orm_filters = []
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

    async def one_equipment(
        self, db: AsyncSession, *, serial_number: str
    ) -> Equipment:

        query = select(Equipment)

        filters = [Equipment.is_deleted == false()]

        if serial_number is not None:
            filters.append(Equipment.serial_number == serial_number)

        return await self._first(db.scalars(query.filter(*filters)))


class ZonePriceRepository(
    CRUDBase[ZonePrice, ZonePriceCreate, ZonePriceUpdate]
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
        if filters.weekday__in:
            orm_filters.append(
                self.model.plan_days.contains(filters.weekday__in)
            )
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


spot_repo = SpotRepository(Spot)
parking_repo = ParkingRepository(Parking)
zone_repo = ZoneRepository(Zone)
equipment_repo = EquipmentRepository(Equipment)
zoneprice_repo = ZonePriceRepository(ZonePrice)
rule_repo = RuleRepository(Rule)
zonerule_repo = ZoneRuleRepository(ZoneRule)
platerule_repo = PlateRuleRepository(PlateRule)
