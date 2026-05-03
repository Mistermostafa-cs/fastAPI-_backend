from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal

# Existing schemas...
class AdminDashboardStats(BaseModel):
    total_students: int
    total_teachers: int
    total_parents: int
    total_users: int
    active_classes: int
    recent_users: List[dict]

class StudentBrief(BaseModel):
    student_id: int
    full_name: str
    roll_number: str
    class_name: Optional[str]
    is_active: bool

class UserAdminResponse(BaseModel):
    user_id: int
    full_name: str
    email: Optional[str] = None
    student_id: Optional[str] = None
    role_name: str
    is_active: bool
    created_at: datetime

class StudentCreateResponse(BaseModel):
    status: str
    message: str
    student_id: str
    username: str
    temporary_password: str

# CRUD Schemas
class StudentCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    roll_number: str
    admission_number: str
    admission_date: date
    address: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None

class TeacherCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    employee_code: str
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    joining_date: Optional[date] = None
    salary: Optional[Decimal] = None
    gender: Optional[str] = None

class ParentCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    occupation: Optional[str] = None
    relationship: Optional[str] = None
    alternate_phone: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = None

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    roll_number: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None

class TeacherUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    salary: Optional[Decimal] = None
    is_active: Optional[bool] = None

class ParentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    occupation: Optional[str] = None
    alternate_phone: Optional[str] = None
    is_active: Optional[bool] = None
