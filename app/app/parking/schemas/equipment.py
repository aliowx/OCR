from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import EquipmentType


class EquipmentBase(BaseModel):
    equipment_type: EquipmentType | None = None
    tag: str | None = None
    serial_number: str | None = None
    ip_address: str | None = None
    parking_id: int | None = None
    zone_id: int | None = None
    additional_data: dict | None = None


class EquipmentCreate(EquipmentBase):
    equipment_type: EquipmentType
    parking_id: int | None = None
    zone_id: int
    tag: str | None = Field(None, max_length=30)
    serial_number: str | None = Field(None, max_length=50)
    ip_address: str | None = Field(None, max_length=15)


class EquipmentUpdate(EquipmentBase):
    tag: str | None = Field(None, max_length=30)
    serial_number: str | None = Field(None, max_length=50)
    ip_address: str | None = Field(None, max_length=15)


class EquipmentInDBBase(EquipmentBase):
    id: int | None = None
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class Equipment(EquipmentInDBBase): ...


class EquipmentInDB(EquipmentInDBBase): ...


class ReadEquipmentsFilter(BaseModel):
    ip_address__eq: str | None = None
    serial_number__eq: str | None = None
    parking_id__eq: int | None = None
    zone_id__eq: int | None = None
    equipment_type__eq: int | None = None
    created__gte: str | None = None
    created__lte: str | None = None
    limit: int | None = 100
    skip: int = 0


class ReadEquipmentsParams(BaseModel):
    ip_address: str | None = None
    serial_number: str | None = None
    parking_id: int | None = None
    zone_id: int | None = None
    equipment_type: EquipmentType | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
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
    def db_filters(self) -> ReadEquipmentsFilter:
        filters = ReadEquipmentsFilter(limit=self.size, skip=self.skip)
        if self.parking_id:
            filters.parking_id__eq = self.parking_id
        if self.ip_address:
            filters.ip_address__eq = self.ip_address
        if self.serial_number:
            filters.serial_number__eq = self.serial_number
        if self.equipment_type:
            filters.equipment_type__eq = self.equipment_type.value
        return filters
