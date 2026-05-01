from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ProfileResponse(BaseModel):
    user_id: int
    role_name: str
    profile: dict


class ProfileUpdateRequest(BaseModel):
    department: str | None = None
    access_level: int | None = None
    qualification: str | None = None
    specialization: str | None = None
    joining_date: date | None = None
    salary: Decimal | None = None
    roll_number: str | None = None
    admission_date: date | None = None
    admission_number: str | None = None
    address: str | None = None
    occupation: str | None = None
    relationship: str | None = None
    alternate_phone: str | None = None
