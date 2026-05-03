from datetime import date, datetime
from pydantic import BaseModel


class AttendanceBase(BaseModel):
    attendance_date: date
    status: str = "Present"
    remarks: str | None = None


class AttendanceIn(AttendanceBase):
    student_id: int
    class_subject_id: int
    marked_by_id: int


class AttendanceOut(AttendanceBase):
    attendance_id: int
    student_id: int
    class_subject_id: int
    marked_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
