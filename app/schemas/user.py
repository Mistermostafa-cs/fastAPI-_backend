from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    user_id: int
    role_id: int
    first_name: str
    last_name: str
    full_name: str
    email: str | None = None
    student_id: str | None = None
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None


class UserCreateRequest(BaseModel):
    role_id: int
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone_number: str | None = None
    gender: str | None = None
    profile_photo: str | None = None
    created_by: int | None = None


class UserUpdateRequest(BaseModel):
    role_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None
    gender: str | None = None
    profile_photo: str | None = None


class UserStatusRequest(BaseModel):
    is_active: bool
