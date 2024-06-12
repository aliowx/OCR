from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import QueryParam, RuleType, Weekday
from app.parking.schemas.parkingzone import ParkingZoneRule
from app.schemas.types import UTCDatetime


class RuleBase(BaseModel):
    name_fa: str | None = None
    rule_type: RuleType | None = None
    weekdays: list[Weekday] | None = Field(default_factory=list)
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    registeration_date: date | None = None


class RuleBaseComplete(RuleBase):
    zones: list["ZoneRuleBase"] | None = Field(default_factory=list)
    plates: list["PlateRuleBase"] | None = Field(default_factory=list)


class RuleCreate(RuleBase):
    name_fa: str
    rule_type: RuleType
    start_datetime: UTCDatetime | None = None
    end_datetime: UTCDatetime | None = None
    zone_ids: list[int] = Field(default_factory=list)


class RuleUpdate(RuleBase): ...


class RuleInDBBase(RuleBaseComplete):
    id: int | None = None
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class Rule(RuleInDBBase): ...


class RuleInDB(RuleInDBBase): ...


class ReadRulesFilter(BaseModel):
    name_fa__eq: str | None = None
    name_fa__contains: str | None = None
    rule_type__eq: int | None = None
    weekday__in: list[Weekday] | None = None
    start_datetime__gte: str | None = None
    start_datetime__lte: str | None = None
    end_datetime__gte: str | None = None
    end_datetime__lte: str | None = None
    registeration_date__gte: str | None = None
    registeration_date__lte: str | None = None
    created__gte: str | None = None
    created__lte: str | None = None
    limit: int | None = 100
    skip: int = 0


class ReadRulesParams(BaseModel):
    name_fa: str | None = None
    rule_type: RuleType | None = Field(
        QueryParam(None, description=str(list(RuleType)))
    )
    weekdays: list[Weekday] = Field(
        QueryParam(default_factory=list, description=str(list(Weekday)))
    )
    start_datetime_from: datetime | None = None
    start_datetime_to: datetime | None = None
    end_datetime_from: datetime | None = None
    end_datetime_to: datetime | None = None
    registeration_date_from: date | None = None
    registeration_date_to: date | None = None
    size: int | None = 100
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip

    @property
    def db_filters(self) -> ReadRulesFilter:
        filters = ReadRulesFilter(limit=self.size, skip=self.skip)
        if self.name_fa:
            filters.name_fa__contains = self.name_fa
        if self.rule_type:
            filters.rule_type__eq = self.rule_type.value
        if self.weekdays:
            filters.weekday__in = self.weekdays
        if self.start_datetime_from:
            filters.start_datetime__gte = self.start_datetime_from
        if self.start_datetime_to:
            filters.start_datetime__lte = self.start_datetime_to
        if self.end_datetime_from:
            filters.end_datetime__gte = self.end_datetime_from
        if self.end_datetime_to:
            filters.end_datetime__lte = self.end_datetime_to
        if self.registeration_date_from:
            filters.registeration_date__gte = self.registeration_date_from
        if self.registeration_date_to:
            filters.registeration_date__lte = self.registeration_date_to
        return filters


class ZoneRuleBase(BaseModel):
    zone_id: int | None = None
    rule_id: int | None = None


class ZoneRuleComplete(ZoneRuleBase):
    zone: ParkingZoneRule | None = None
    rule: Rule | None = None


class ZoneRuleCreate(ZoneRuleBase):
    zone_id: int
    rule_id: int


class ZoneRuleUpdate(ZoneRuleBase): ...


class ZoneRuleInDBBase(ZoneRuleComplete):
    id: int | None = None
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class ZoneRule(ZoneRuleInDBBase): ...


class ZoneRuleInDB(ZoneRuleInDBBase): ...


class PlateRuleBase(BaseModel):
    plate: str | None = None
    rule_id: int | None = None


class PlateRuleComplete(PlateRuleBase):
    rule: Rule | None = None


class PlateRuleCreate(PlateRuleBase):
    plate: str
    rule_id: int


class PlateRuleUpdate(PlateRuleBase): ...


class PlateRuleInDBBase(PlateRuleComplete):
    id: int | None = None
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class PlateRule(PlateRuleInDBBase): ...


class PlateRuleInDB(PlateRuleInDBBase): ...


class SetZoneRuleInput(BaseModel):
    rule_id: int
    zone_ids: list[int] = Field(default_factory=list)


class SetPlateRuleInput(BaseModel):
    rule_id: int
    plates: list[str] = Field(default_factory=list)
