"""
app/schemas/grade_setup.py
--------------------------
Schemas for the "one-form grade setup" workflow and auto-enrollment.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Grade Level Setup – single form to configure everything
# ---------------------------------------------------------------------------

class TermSubjectsIn(BaseModel):
    """Subjects to assign to a specific term within a grade level."""
    term_number: int        # 1 or 2
    subject_ids: list[int]  # list of existing Subject IDs
    teacher_id: int         # one teacher per term (can be overridden per subject later)


class GradeLevelSetupIn(BaseModel):
    """
    One-form setup: AcademicYear + GradeLevel + Terms + Subjects.

    Creates (or reuses) the Class row for the grade, then assigns subjects
    per term via SubjectOffering.
    """
    academic_year_id: int
    grade_level: int          # e.g. 7, 8, 9 …
    class_name: str           # e.g. "Grade 7"
    terms: list[TermSubjectsIn]


class TermSubjectsOut(BaseModel):
    term_id: int
    term_name: str
    term_number: int
    offerings_created: int
    offerings_skipped: int


class GradeLevelSetupOut(BaseModel):
    class_id: int
    class_name: str
    grade_level: int
    academic_year_id: int
    terms: list[TermSubjectsOut]


# ---------------------------------------------------------------------------
# Auto-Enrollment by Grade Level
# ---------------------------------------------------------------------------

class GradeLevelEnrollIn(BaseModel):
    """Enroll a student in all subjects for a given grade level + academic year."""
    student_id: int
    academic_year_id: int
    grade_level: int
    enrollment_date: date
    status: str = "Active"


class GradeLevelEnrollOut(BaseModel):
    student_id: int
    class_id: int
    class_name: str
    enrollment_id: int
    grade_level: int
    academic_year_id: int
    total_subjects: int
    terms_summary: list[TermSubjectsOut]


# ---------------------------------------------------------------------------
# Lookup: subjects by grade level (for the enrollment form dropdown)
# ---------------------------------------------------------------------------

class SubjectSummary(BaseModel):
    subject_id: int
    subject_code: str
    subject_name: str
    term_number: int
    term_name: str
    offering_id: int


class GradeLevelSubjectsOut(BaseModel):
    class_id: int
    class_name: str
    grade_level: int
    academic_year_id: int
    subjects: list[SubjectSummary]
