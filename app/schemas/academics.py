from datetime import date, datetime

from pydantic import BaseModel


class AcademicYearIn(BaseModel):
    year_label: str
    start_date: date
    end_date: date
    is_current: bool = False


class AcademicYearOut(BaseModel):
    academic_year_id: int
    year_label: str
    start_date: date
    end_date: date
    is_current: bool
    created_at: datetime


class ClassIn(BaseModel):
    class_name: str
    grade_level: int
    section: str | None = None
    academic_year_id: int
    class_teacher_id: int | None = None
    max_capacity: int | None = None
    room_number: str | None = None


class ClassOut(BaseModel):
    class_id: int
    class_name: str
    grade_level: int
    section: str | None = None
    academic_year_id: int
    class_teacher_id: int | None = None
    max_capacity: int | None = None
    room_number: str | None = None


class SubjectIn(BaseModel):
    subject_code: str
    subject_name: str
    description: str | None = None
    credit_hours: int | None = None
    is_elective: bool = False


class SubjectOut(BaseModel):
    subject_id: int
    subject_code: str
    subject_name: str
    description: str | None = None
    credit_hours: int | None = None
    is_elective: bool


class ClassSubjectIn(BaseModel):
    class_id: int
    subject_id: int
    teacher_id: int
    academic_year_id: int


class ClassSubjectOut(BaseModel):
    class_subject_id: int
    class_id: int
    subject_id: int
    teacher_id: int
    academic_year_id: int


class EnrollmentIn(BaseModel):
    student_id: int
    class_id: int
    academic_year_id: int
    enrollment_date: date
    status: str = "Active"


class EnrollmentOut(BaseModel):
    enrollment_id: int
    student_id: int
    class_id: int
    academic_year_id: int
    enrollment_date: date
    status: str
