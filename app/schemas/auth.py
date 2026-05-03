from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: str  # This will be the identifier (email or student_id)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    full_name: str
    email: str | None = None
    student_id: str | None = None
    role_name: str
    must_change_password: bool = False


class AuthUserResponse(BaseModel):
    user_id: int
    full_name: str
    email: str | None = None
    student_id: str | None = None
    role_id: int
    role_name: str
    is_active: bool
    must_change_password: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
