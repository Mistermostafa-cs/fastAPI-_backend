from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class GradeScaleOut(BaseModel):
    grade_scale_id: int
    grade_letter: str
    min_percentage: Decimal
    max_percentage: Decimal
    grade_point: Decimal | None = None
    remarks: str | None = None

    class Config:
        from_attributes = True


class GradeBase(BaseModel):
    marks_obtained: Decimal
    total_marks: Decimal
    remarks: str | None = None


class GradeIn(GradeBase):
    student_id: int
    class_subject_id: int
    academic_year_id: int
    exam_id: int | None = None
    input_by_id: int
    is_passed: bool | None = None
    grade_scale_id: int | None = None


class GradeOut(GradeBase):
    grade_id: int
    student_id: int
    class_subject_id: int
    academic_year_id: int
    exam_id: int | None = None
    percentage: Decimal | None = None
    is_passed: bool | None = None
    grade_scale_id: int | None = None
    input_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
