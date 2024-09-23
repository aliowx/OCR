from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.base import EquipmentStatus, EquipmentType, QueryParam


class EquipmentBase(BaseModel):
    equipment_type: EquipmentType = None
    equipment_status: EquipmentStatus = None
    serial_number: str | None = None
    ip_address: str | None = None
    zone_id: int | None = None
    zone_detail: dict | None = None
    image_id: int | None = None
    tag: str | None = None
    additional_data: dict | None = None


class EquipmentCreate(BaseModel):
    equipment_type: EquipmentType
    equipment_status: EquipmentStatus
    serial_number: str = Field(None, max_length=50)
    ip_address: str
    zone_id: int
    tag:str
    


class EquipmentUpdate(EquipmentBase):...


class EquipmentInDBBase(EquipmentBase):
    id: int | None = None
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class Equipment(EquipmentInDBBase): ...


class EquipmentInDB(EquipmentInDBBase): ...


class FilterEquipmentsParams(BaseModel):
    ip_address: str | None = None
    serial_number: str | None = None
    zone_id: int | None = None
    equipment_type: EquipmentType  = None
    equipment_status: EquipmentStatus = None 
    tag: str | None = None
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
