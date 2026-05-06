from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class AssignmentBase(BaseModel):
    title: str
    description: str | None = None
    due_date: datetime
    max_marks: Decimal = Decimal("100.00")


class AssignmentIn(AssignmentBase):
    class_subject_id: int
    created_by_id: int


class AssignmentOut(AssignmentBase):
    assignment_id: int
    class_subject_id: int
    created_by_id: int
    file_path: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssignmentSubmissionBase(BaseModel):
    comments: str | None = None


class AssignmentSubmissionIn(AssignmentSubmissionBase):
    assignment_id: int
    student_id: int


class AssignmentSubmissionOut(AssignmentSubmissionBase):
    submission_id: int
    assignment_id: int
    student_id: int
    submitted_at: datetime
    file_path: str | None = None
    marks_obtained: Decimal | None = None
    graded_by_id: int | None = None
    graded_at: datetime | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssignmentGradeIn(BaseModel):
    marks_obtained: Decimal
    graded_by_id: int
    comments: str | None = None
    status: str = "Graded"
