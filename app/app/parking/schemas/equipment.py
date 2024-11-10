from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from app.models.base import EquipmentStatus, EquipmentType
from app.parking.schemas.zone import Zone


class EquipmentBase(BaseModel):
    equipment_type: Optional[EquipmentType] = None
    equipment_status: Optional[EquipmentStatus] = None
    serial_number: str | None = None
    ip_address: str | None = None
    zone_id: int | None = None
    image_id: int | None = None
    tag: str | None = None
    additional_data: dict | None = None


class EquipmentCreate(BaseModel):
    equipment_type: Optional[EquipmentType]
    equipment_status: Optional[EquipmentStatus]
    serial_number: str = Field(None, max_length=50)
    ip_address: str
    tag: str
    zone_id: int | None = None
    additional_data: dict | None = None


class EquipmentUpdate(EquipmentBase): ...


class EquipmentInDBBase(EquipmentBase):
    id: int | None = None
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class Equipment(EquipmentInDBBase):
    zone: Zone | None = None


class EquipmentInDB(EquipmentInDBBase): ...


class FilterEquipmentsParams(BaseModel):
    ip_address: str | None = None
    serial_number: str | None = None
    zone_id: int | None = None
    equipment_status: Optional[EquipmentStatus] = None
    tag: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    size: int | None = None
    page: int = 1
    asc: bool = True

    @property
    def skip(self) -> int:
        skip = 0
        if self.size is not None:
            skip = (self.page * self.size) - self.size
        return skip
