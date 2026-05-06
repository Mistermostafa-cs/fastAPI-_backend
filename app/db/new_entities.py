"""
new_entities.py
---------------
New SQLAlchemy models for the Term / SubjectOffering refactor.

These models are ADDITIVE – they do not touch any existing table.
Import this module alongside entities.py so that Base.metadata knows
about both sets of tables at create_all() time.

Usage in app/db/models.py:
    from app.db.entities import Base          # existing
    from app.db.new_entities import Term, SubjectOffering   # new
    # Base is shared via inheritance, so create_all covers everything.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Re-use the SAME Base that all existing models use so that
# create_all() covers everything in one call.
from app.db.entities import Base


class Term(Base):
    """A single academic term (e.g. Term 1 / Term 2) within an AcademicYear."""

    __tablename__ = "Terms"

    TermID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    AcademicYearID: Mapped[int] = mapped_column(
        ForeignKey("AcademicYears.AcademicYearID"), nullable=False
    )
    TermName: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "Term 1"
    TermNumber: Mapped[int] = mapped_column(nullable=False)            # 1 or 2
    StartDate: Mapped[date] = mapped_column(Date, nullable=False)
    EndDate: Mapped[date] = mapped_column(Date, nullable=False)
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("AcademicYearID", "TermNumber", name="uq_term_year_number"),
    )

    # relationships
    AcademicYear: Mapped["app.db.entities.AcademicYear"] = relationship(  # type: ignore[name-defined]
        "AcademicYear", foreign_keys=[AcademicYearID]
    )
    SubjectOfferings: Mapped[list[SubjectOffering]] = relationship(
        back_populates="Term"
    )


class SubjectOffering(Base):
    """
    A subject offered to a specific class within a specific term.

    Replaces the old ClassSubjects.AcademicYearID-based lookup for
    term-aware subject scheduling.  The old ClassSubjects table is left
    intact so existing grades / exams / attendance records keep working.
    """

    __tablename__ = "SubjectOfferings"

    OfferingID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    SubjectID: Mapped[int] = mapped_column(
        ForeignKey("Subjects.SubjectID"), nullable=False
    )
    TermID: Mapped[int] = mapped_column(
        ForeignKey("Terms.TermID"), nullable=False
    )
    ClassID: Mapped[int] = mapped_column(
        ForeignKey("Classes.ClassID"), nullable=False
    )
    TeacherID: Mapped[int] = mapped_column(
        ForeignKey("TeacherProfiles.TeacherID"), nullable=False
    )
    # Optional back-link to the legacy ClassSubject row so we can track
    # which old record this offering was migrated from.
    LegacyClassSubjectID: Mapped[int | None] = mapped_column(
        ForeignKey("ClassSubjects.ClassSubjectID"), nullable=True
    )
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "SubjectID", "TermID", "ClassID",
            name="uq_offering_subject_term_class"
        ),
    )

    # relationships
    Subject: Mapped["app.db.entities.Subject"] = relationship(  # type: ignore[name-defined]
        "Subject", foreign_keys=[SubjectID]
    )
    Term: Mapped[Term] = relationship(back_populates="SubjectOfferings")
    Class: Mapped["app.db.entities.Class"] = relationship(  # type: ignore[name-defined]
        "Class", foreign_keys=[ClassID]
    )
    TeacherProfile: Mapped["app.db.entities.TeacherProfile"] = relationship(  # type: ignore[name-defined]
        "TeacherProfile", foreign_keys=[TeacherID]
    )
