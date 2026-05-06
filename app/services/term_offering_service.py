"""
app/services/term_offering_service.py
--------------------------------------
Business logic for:
  1. Auto-creating 2 Terms when a new AcademicYear is created.
  2. Querying subjects via SubjectOffering (new path).
  3. Migrating existing ClassSubject rows into SubjectOfferings (one-time helper).
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.db.entities import AcademicYear, ClassSubject, Subject
from app.db.new_entities import SubjectOffering, Term
from app.schemas.term_offerings import MigrationResult, SubjectOfferingOut

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Term auto-creation
# ---------------------------------------------------------------------------

def create_default_terms(db: Session, academic_year: AcademicYear) -> list[Term]:
    """
    Create Term 1 and Term 2 for a freshly created AcademicYear.

    The year is split in half:
        Term 1 → start_date  …  midpoint
        Term 2 → midpoint+1  …  end_date

    Returns the two persisted Term objects.
    """
    start = academic_year.StartDate
    end = academic_year.EndDate
    now = datetime.now(timezone.utc)

    total_days = (end - start).days
    mid_offset = math.floor(total_days / 2)

    from datetime import timedelta
    mid = start + timedelta(days=mid_offset)
    mid_next = mid + timedelta(days=1)

    terms = [
        Term(
            AcademicYearID=academic_year.AcademicYearID,
            TermName="Term 1",
            TermNumber=1,
            StartDate=start,
            EndDate=mid,
            IsActive=True,
            CreatedAt=now,
            UpdatedAt=now,
        ),
        Term(
            AcademicYearID=academic_year.AcademicYearID,
            TermName="Term 2",
            TermNumber=2,
            StartDate=mid_next,
            EndDate=end,
            IsActive=True,
            CreatedAt=now,
            UpdatedAt=now,
        ),
    ]
    db.add_all(terms)
    db.flush()   # get TermIDs without committing – caller owns the transaction
    return terms


# ---------------------------------------------------------------------------
# Subject query via SubjectOffering (new path)
# ---------------------------------------------------------------------------

def get_subjects_by_term(
    db: Session,
    term_id: int,
    class_id: int | None = None,
) -> list[SubjectOfferingOut]:
    """
    Fetch subjects offered in a given term, optionally filtered by class.
    Returns enriched SubjectOfferingOut objects.
    """
    query = (
        db.query(SubjectOffering)
        .filter(SubjectOffering.TermID == term_id, SubjectOffering.IsActive == True)
    )
    if class_id is not None:
        query = query.filter(SubjectOffering.ClassID == class_id)

    rows = query.all()
    result = []
    for row in rows:
        # eager-load related objects (already accessible via SQLAlchemy lazy load)
        subject = row.Subject
        term = row.Term
        cls = row.Class
        teacher_user = row.TeacherProfile.User if row.TeacherProfile else None

        result.append(
            SubjectOfferingOut(
                offering_id=row.OfferingID,
                subject_id=row.SubjectID,
                term_id=row.TermID,
                class_id=row.ClassID,
                teacher_id=row.TeacherID,
                legacy_class_subject_id=row.LegacyClassSubjectID,
                is_active=row.IsActive,
                subject_name=subject.SubjectName if subject else None,
                subject_code=subject.SubjectCode if subject else None,
                term_name=term.TermName if term else None,
                class_name=cls.ClassName if cls else None,
                teacher_name=(
                    f"{teacher_user.FirstName} {teacher_user.LastName}"
                    if teacher_user
                    else None
                ),
            )
        )
    return result


def get_subjects_by_class_and_academic_year(
    db: Session,
    class_id: int,
    academic_year_id: int,
) -> list[SubjectOfferingOut]:
    """
    New equivalent of the old ClassSubject query for a class + year.
    Returns all offerings across both terms for the given class/year.
    """
    term_ids = [
        t.TermID
        for t in db.query(Term.TermID)
        .filter(Term.AcademicYearID == academic_year_id)
        .all()
    ]
    if not term_ids:
        return []

    rows = (
        db.query(SubjectOffering)
        .filter(
            SubjectOffering.ClassID == class_id,
            SubjectOffering.TermID.in_(term_ids),
            SubjectOffering.IsActive == True,
        )
        .all()
    )

    result = []
    for row in rows:
        subject = row.Subject
        term = row.Term
        cls = row.Class
        teacher_user = row.TeacherProfile.User if row.TeacherProfile else None
        result.append(
            SubjectOfferingOut(
                offering_id=row.OfferingID,
                subject_id=row.SubjectID,
                term_id=row.TermID,
                class_id=row.ClassID,
                teacher_id=row.TeacherID,
                legacy_class_subject_id=row.LegacyClassSubjectID,
                is_active=row.IsActive,
                subject_name=subject.SubjectName if subject else None,
                subject_code=subject.SubjectCode if subject else None,
                term_name=term.TermName if term else None,
                class_name=cls.ClassName if cls else None,
                teacher_name=(
                    f"{teacher_user.FirstName} {teacher_user.LastName}"
                    if teacher_user
                    else None
                ),
            )
        )
    return result


# ---------------------------------------------------------------------------
# Migration helper – copy ClassSubjects → SubjectOfferings (Term 1)
# ---------------------------------------------------------------------------

def migrate_class_subjects_to_offerings(
    db: Session,
    academic_year_id: int | None = None,
    dry_run: bool = False,
) -> MigrationResult:
    """
    One-time migration helper.

    For every existing ClassSubject row (optionally filtered by academic_year_id),
    finds (or creates) the corresponding Term 1 for that academic year and inserts
    a matching SubjectOffering row.

    Args:
        db:               SQLAlchemy session.
        academic_year_id: Restrict migration to a single academic year.
                          Pass None to migrate all years.
        dry_run:          When True, builds the objects but rolls back instead
                          of committing – useful for previewing counts.

    Returns:
        MigrationResult with counts.
    """
    query = db.query(ClassSubject)
    if academic_year_id is not None:
        query = query.filter(ClassSubject.AcademicYearID == academic_year_id)

    class_subjects = query.all()

    migrated = 0
    skipped = 0
    errors: list[str] = []
    now = datetime.now(timezone.utc)

    # Cache: academic_year_id → Term 1 object
    term1_cache: dict[int, Term] = {}

    for cs in class_subjects:
        try:
            yr_id = cs.AcademicYearID

            # Resolve Term 1 for this academic year (create if missing)
            if yr_id not in term1_cache:
                term1 = (
                    db.query(Term)
                    .filter(Term.AcademicYearID == yr_id, Term.TermNumber == 1)
                    .first()
                )
                if term1 is None:
                    # Fetch the parent AcademicYear to compute date ranges
                    ay = db.query(AcademicYear).filter(
                        AcademicYear.AcademicYearID == yr_id
                    ).first()
                    if ay is None:
                        errors.append(
                            f"ClassSubject {cs.ClassSubjectID}: "
                            f"AcademicYear {yr_id} not found – skipped."
                        )
                        skipped += 1
                        continue
                    [term1, _] = create_default_terms(db, ay)
                term1_cache[yr_id] = term1

            t1 = term1_cache[yr_id]

            # Skip if an identical offering already exists
            exists = (
                db.query(SubjectOffering)
                .filter(
                    SubjectOffering.SubjectID == cs.SubjectID,
                    SubjectOffering.TermID == t1.TermID,
                    SubjectOffering.ClassID == cs.ClassID,
                )
                .first()
            )
            if exists:
                skipped += 1
                continue

            offering = SubjectOffering(
                SubjectID=cs.SubjectID,
                TermID=t1.TermID,
                ClassID=cs.ClassID,
                TeacherID=cs.TeacherID,
                LegacyClassSubjectID=cs.ClassSubjectID,
                IsActive=True,
                CreatedAt=now,
                UpdatedAt=now,
            )
            db.add(offering)
            migrated += 1

        except Exception as exc:  # noqa: BLE001
            errors.append(f"ClassSubject {cs.ClassSubjectID}: {exc}")
            skipped += 1

    if dry_run:
        db.rollback()
    else:
        db.commit()

    return MigrationResult(migrated=migrated, skipped=skipped, errors=errors)
