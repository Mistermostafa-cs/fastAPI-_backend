from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from typing import List


class ExamTypeOut(BaseModel):
    exam_type_id: int
    type_name: str

    class Config:
        from_attributes = True


class ExamBase(BaseModel):
    title: str
    description: str | None = None
    exam_date: datetime
    duration_minutes: int = 60
    total_marks: Decimal = Decimal("100.00")
    passing_marks: Decimal = Decimal("40.00")
    is_online: bool = True


class OptionCreate(BaseModel):
    option_text: str
    is_correct: bool = False
    option_order: int = 1

class QuestionCreate(BaseModel):
    question_text: str
    question_type_id: int = 1
    marks: Decimal = Decimal("1.00")
    difficulty_level: int | None = None
    explanation: str | None = None
    options: List[OptionCreate]

class ExamCreate(ExamBase):
    class_subject_id: int
    exam_type_id: int = 1
    questions: List[QuestionCreate]

class ExamIn(ExamBase):
    class_subject_id: int
    exam_type_id: int
    created_by_id: int
    questions: List[QuestionCreate] | None = None


class ExamOut(ExamBase):
    exam_id: int
    class_subject_id: int
    exam_type_id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OptionBase(BaseModel):
    option_text: str
    is_correct: bool = False
    option_order: int = 1


class OptionIn(OptionBase):
    question_id: int


class OptionOut(OptionBase):
    option_id: int
    question_id: int

    class Config:
        from_attributes = True


class QuestionBase(BaseModel):
    question_text: str
    question_order: int = 1
    marks: Decimal = Decimal("1.00")
    difficulty_level: int | None = None
    explanation: str | None = None


class QuestionIn(QuestionBase):
    exam_id: int
    question_type_id: int


class QuestionOut(QuestionBase):
    question_id: int
    exam_id: int
    question_type_id: int
    options: List[OptionOut] = []

    class Config:
        from_attributes = True


class ExamSessionBase(BaseModel):
    pass


class ExamSessionIn(ExamSessionBase):
    exam_id: int
    student_id: int


class ExamSessionOut(ExamSessionBase):
    session_id: int
    exam_id: int
    student_id: int
    started_at: datetime
    submitted_at: datetime | None = None
    total_score: Decimal | None = None
    is_passed: bool | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StudentAnswerIn(BaseModel):
    question_id: int
    selected_option_id: int | None = None
    answer_text: str | None = None


class ExamSubmissionIn(BaseModel):
    session_id: int
    answers: List[StudentAnswerIn]
