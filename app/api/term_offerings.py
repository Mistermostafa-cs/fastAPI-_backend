"""
app/api/term_offerings.py
--------------------------
New API endpoints for Terms and SubjectOfferings.
Existing /academics/* endpoints are untouched.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.entities import AcademicYear
from app.db.new_entities import SubjectOffering, Term
from app.db.session import get_db
from app.schemas.term_offerings import (
    MigrationResult,
    SubjectOfferingIn,
    SubjectOfferingOut,
    TermIn,
    TermOut,
)
from app.services.term_offering_service import (
    create_default_terms,
    get_subjects_by_class_and_academic_year,
    get_subjects_by_term,
    migrate_class_subjects_to_offerings,
)

router = APIRouter(prefix="/v2/academics", tags=["Academics v2"])


# ---------------------------------------------------------------------------
# Terms
# ---------------------------------------------------------------------------

@router.get("/terms", response_model=list[TermOut])
def list_terms(
    academic_year_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> list[TermOut]:
    """List all terms, optionally filtered by academic year."""
    query = db.query(Term)
    if academic_year_id is not None:
        query = query.filter(Term.AcademicYearID == academic_year_id)
    rows = query.order_by(Term.AcademicYearID.desc(), Term.TermNumber).all()
    return [
        TermOut(
            term_id=r.TermID,
            academic_year_id=r.AcademicYearID,
            term_name=r.TermName,
            term_number=r.TermNumber,
            start_date=r.StartDate,
            end_date=r.EndDate,
            is_active=r.IsActive,
            created_at=r.CreatedAt,
        )
        for r in rows
    ]


@router.post("/terms", response_model=TermOut, status_code=status.HTTP_201_CREATED)
def create_term(
    academic_year_id: int = Form(...),
    term_name: str = Form(...),
    term_number: int = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> TermOut:
    """Manually create a term (prefer the academic-year auto-creation flow)."""
    from datetime import date as date_type

    ay = db.query(AcademicYear).filter(
        AcademicYear.AcademicYearID == academic_year_id
    ).first()
    if ay is None:
        raise HTTPException(status_code=404, detail="Academic year not found")

    now = datetime.now(timezone.utc)
    row = Term(
        AcademicYearID=academic_year_id,
        TermName=term_name,
        TermNumber=term_number,
        StartDate=date_type.fromisoformat(start_date),
        EndDate=date_type.fromisoformat(end_date),
        IsActive=is_active,
        CreatedAt=now,
        UpdatedAt=now,
    )
    db.add(row)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create term") from exc
    db.refresh(row)
    return TermOut(
        term_id=row.TermID,
        academic_year_id=row.AcademicYearID,
        term_name=row.TermName,
        term_number=row.TermNumber,
        start_date=row.StartDate,
        end_date=row.EndDate,
        is_active=row.IsActive,
        created_at=row.CreatedAt,
    )


@router.post(
    "/academic-years/{academic_year_id}/init-terms",
    response_model=list[TermOut],
    status_code=status.HTTP_201_CREATED,
)
def init_terms_for_year(
    academic_year_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> list[TermOut]:
    """
    Auto-create Term 1 and Term 2 for an existing academic year.
    Raises 409 if terms already exist for this year.
    """
    ay = db.query(AcademicYear).filter(
        AcademicYear.AcademicYearID == academic_year_id
    ).first()
    if ay is None:
        raise HTTPException(status_code=404, detail="Academic year not found")

    existing = (
        db.query(Term)
        .filter(Term.AcademicYearID == academic_year_id)
        .count()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Terms already exist for academic year {academic_year_id}",
        )

    terms = create_default_terms(db, ay)
    db.commit()
    return [
        TermOut(
            term_id=t.TermID,
            academic_year_id=t.AcademicYearID,
            term_name=t.TermName,
            term_number=t.TermNumber,
            start_date=t.StartDate,
            end_date=t.EndDate,
            is_active=t.IsActive,
            created_at=t.CreatedAt,
        )
        for t in terms
    ]


# ---------------------------------------------------------------------------
# Subject Offerings
# ---------------------------------------------------------------------------

@router.get("/subject-offerings", response_model=list[SubjectOfferingOut])
def list_subject_offerings(
    term_id: Optional[int] = None,
    class_id: Optional[int] = None,
    academic_year_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> list[SubjectOfferingOut]:
    """
    List subject offerings.

    Filter options:
    - term_id                              → offerings for a specific term
    - term_id + class_id                   → offerings for a term & class
    - academic_year_id + class_id          → all offerings for a class across the year
    """
    if academic_year_id is not None and class_id is not None:
        return get_subjects_by_class_and_academic_year(db, class_id, academic_year_id)

    if term_id is not None:
        return get_subjects_by_term(db, term_id, class_id)

    # No filters: return all (admin overview)
    rows = db.query(SubjectOffering).order_by(SubjectOffering.OfferingID.desc()).all()
    return [
        SubjectOfferingOut(
            offering_id=r.OfferingID,
            subject_id=r.SubjectID,
            term_id=r.TermID,
            class_id=r.ClassID,
            teacher_id=r.TeacherID,
            legacy_class_subject_id=r.LegacyClassSubjectID,
            is_active=r.IsActive,
        )
        for r in rows
    ]


@router.post(
    "/subject-offerings",
    response_model=SubjectOfferingOut,
    status_code=status.HTTP_201_CREATED,
)
def create_subject_offering(
    subject_id: int = Form(...),
    term_id: int = Form(...),
    class_id: int = Form(...),
    teacher_id: int = Form(...),
    legacy_class_subject_id: Optional[int] = Form(None),
    is_active: bool = Form(True),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> SubjectOfferingOut:
    """Create a new subject offering for a given term and class."""
    # Verify term exists
    term = db.query(Term).filter(Term.TermID == term_id).first()
    if term is None:
        raise HTTPException(status_code=404, detail="Term not found")

    now = datetime.now(timezone.utc)
    row = SubjectOffering(
        SubjectID=subject_id,
        TermID=term_id,
        ClassID=class_id,
        TeacherID=teacher_id,
        LegacyClassSubjectID=legacy_class_subject_id,
        IsActive=is_active,
        CreatedAt=now,
        UpdatedAt=now,
    )
    db.add(row)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Could not create subject offering (duplicate?)"
        ) from exc
    db.refresh(row)
    return SubjectOfferingOut(
        offering_id=row.OfferingID,
        subject_id=row.SubjectID,
        term_id=row.TermID,
        class_id=row.ClassID,
        teacher_id=row.TeacherID,
        legacy_class_subject_id=row.LegacyClassSubjectID,
        is_active=row.IsActive,
    )


@router.patch("/subject-offerings/{offering_id}/deactivate", response_model=SubjectOfferingOut)
def deactivate_subject_offering(
    offering_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> SubjectOfferingOut:
    row = db.query(SubjectOffering).filter(
        SubjectOffering.OfferingID == offering_id
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Subject offering not found")
    row.IsActive = False
    row.UpdatedAt = datetime.now(timezone.utc)
    db.commit()
    db.refresh(row)
    return SubjectOfferingOut(
        offering_id=row.OfferingID,
        subject_id=row.SubjectID,
        term_id=row.TermID,
        class_id=row.ClassID,
        teacher_id=row.TeacherID,
        legacy_class_subject_id=row.LegacyClassSubjectID,
        is_active=row.IsActive,
    )


# ---------------------------------------------------------------------------
# Migration endpoint
# ---------------------------------------------------------------------------

@router.post("/migrations/class-subjects-to-offerings", response_model=MigrationResult)
def run_migration(
    academic_year_id: Optional[int] = None,
    dry_run: bool = False,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> MigrationResult:
    """
    One-time migration: copy ClassSubject rows into SubjectOfferings.

    - academic_year_id: restrict to a single year (omit for all years).
    - dry_run=true: preview counts without writing to the database.
    """
    return migrate_class_subjects_to_offerings(
        db=db,
        academic_year_id=academic_year_id,
        dry_run=dry_run,
    )
