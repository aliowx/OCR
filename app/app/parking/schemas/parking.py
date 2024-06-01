from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.base import UserType


class Beneficiary(BaseModel):
    company_name: str | None = None
    company_register_code: str | None = None
    company_national_code: str | None = None
    company_economic_code: str | None = None
    company_email: str | None = None
    company_phone_number: str | None = None
    company_postal_code: str | None = None
    company_sheba_number: str | None = None
    company_address: str | None = None
    beneficiary_type: UserType | None = None


class ParkingBase(BaseModel):
    name: str | None = None
    brand_name: str | None = None
    floor_count: int | None = None
    area: int | None = None
    location_lat: float | None = None
    location_lon: float | None = None
    parking_address: str | None = None
    parking_logo_base64: str | None = None
    owner_first_name: str | None = None
    owner_last_name: str | None = None
    owner_national_id: str | None = None
    owner_postal_code: str | None = None
    owner_phone_number: str | None = None
    owner_email: str | None = None
    owner_sheba_number: str | None = None
    owner_address: str | None = None
    owner_type: UserType | None = None
    beneficiary_data: Beneficiary | None = None


class ParkingCreate(ParkingBase): ...


class ParkingUpdate(ParkingBase): ...


class ParkingInDBBase(ParkingBase):
    id: int | None = None
    created: datetime
    modified: datetime

    model_config = ConfigDict(from_attributes=True)


class Parking(ParkingInDBBase): ...


class ParkingInDB(ParkingInDBBase): ...
