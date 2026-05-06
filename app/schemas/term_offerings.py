"""
app/schemas/term_offerings.py
------------------------------
Pydantic schemas for the new Term / SubjectOffering models.
Existing academics.py schemas are untouched.
"""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Term
# ---------------------------------------------------------------------------

class TermOut(BaseModel):
    term_id: int
    academic_year_id: int
    term_name: str
    term_number: int
    start_date: date
    end_date: date
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TermIn(BaseModel):
    """Manually create a term (auto-creation via AcademicYear endpoint is preferred)."""
    academic_year_id: int
    term_name: str
    term_number: int = Field(..., ge=1)
    start_date: date
    end_date: date
    is_active: bool = True


# ---------------------------------------------------------------------------
# SubjectOffering
# ---------------------------------------------------------------------------

class SubjectOfferingOut(BaseModel):
    offering_id: int
    subject_id: int
    term_id: int
    class_id: int
    teacher_id: int
    legacy_class_subject_id: int | None = None
    is_active: bool

    # enriched fields (populated by service layer, optional)
    subject_name: str | None = None
    subject_code: str | None = None
    term_name: str | None = None
    class_name: str | None = None
    teacher_name: str | None = None

    class Config:
        from_attributes = True


class SubjectOfferingIn(BaseModel):
    subject_id: int
    term_id: int
    class_id: int
    teacher_id: int
    legacy_class_subject_id: int | None = None
    is_active: bool = True


# ---------------------------------------------------------------------------
# Migration result summary
# ---------------------------------------------------------------------------

class MigrationResult(BaseModel):
    migrated: int
    skipped: int
    errors: list[str] = []
