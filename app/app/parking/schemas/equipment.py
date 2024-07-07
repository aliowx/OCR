from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import EquipmentStatus, EquipmentType, QueryParam


class EquipmentBase(BaseModel):
    equipment_type: EquipmentType | None = None
    equipment_status: EquipmentStatus | None = None
    serial_number: str | None = None
    ip_address: str | None = None
    zone_id: int | None = None
    image_id: int | None = None
    additional_data: dict | None = None


class EquipmentCreate(EquipmentBase):
    equipment_type: EquipmentType
    zone_id: int
    serial_number: str | None = Field(None, max_length=50)
    ip_address: str | None = Field(None, max_length=15)


class EquipmentUpdate(EquipmentBase):
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
    zone_id__eq: int | None = None
    equipment_type__eq: int | None = None
    equipment_status__eq: int | None = None
    created__gte: str | None = None
    created__lte: str | None = None
    limit: int | None = 100
    skip: int = 0


class ReadEquipmentsParams(BaseModel):
    ip_address: str | None = None
    serial_number: str | None = None
    zone_id: int | None = None
    equipment_type: EquipmentType | None = Field(
        QueryParam(None, description=str(list(EquipmentType)))
    )
    equipment_status: EquipmentStatus | None = Field(
        QueryParam(None, description=str(list(EquipmentStatus)))
    )
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
        if self.ip_address:
            filters.ip_address__eq = self.ip_address
        if self.zone_id:
            filters.zone_id__eq = self.zone_id
        if self.serial_number:
            filters.serial_number__eq = self.serial_number
        if self.equipment_type:
            filters.equipment_type__eq = self.equipment_type
        if self.equipment_status:
            filters.equipment_status__eq = self.equipment_status
        if self.start_date:
            filters.created__gte = self.start_date
        if self.end_date:
            filters.created__lte = self.end_date
        return filters
