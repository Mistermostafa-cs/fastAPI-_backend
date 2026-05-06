"""
app/api/grade_setup.py
-----------------------
One-form grade setup + auto-enrollment by grade level.

New endpoints
─────────────
POST /v2/academics/grade-setup
    Create (or reuse) a Class for a grade, then assign subjects per term
    in a single request – no need to touch /academics/classes,
    /v2/academics/subject-offerings, etc. one-by-one.

GET  /v2/academics/grade-levels
    List all grade levels (distinct) for a given academic year.

GET  /v2/academics/grade-levels/{grade_level}/subjects
    Show all subjects assigned to a grade level across both terms
    (used to preview what a student will be enrolled in).

POST /v2/academics/enroll-by-grade
    Enroll a student in a class just by choosing their grade level.
    The endpoint looks up the Class row for that grade/year,
    creates the Enrollment, and returns a full summary.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.entities import AcademicYear, Class, Enrollment, Subject
from app.db.new_entities import SubjectOffering, Term
from app.db.session import get_db
from app.schemas.grade_setup import (
    GradeLevelEnrollIn,
    GradeLevelEnrollOut,
    GradeLevelSetupIn,
    GradeLevelSetupOut,
    GradeLevelSubjectsOut,
    SubjectSummary,
    TermSubjectsOut,
)

router = APIRouter(prefix="/v2/academics", tags=["Grade Setup & Enrollment"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get_or_create_class(db: Session, academic_year_id: int, grade_level: int, class_name: str) -> Class:
    """Return the existing Class for this grade/year or create a new one."""
    existing = (
        db.query(Class)
        .filter(
            Class.AcademicYearID == academic_year_id,
            Class.GradeLevel == grade_level,
        )
        .first()
    )
    if existing:
        return existing

    now = datetime.now(timezone.utc)
    cls = Class(
        ClassName=class_name,
        GradeLevel=grade_level,
        AcademicYearID=academic_year_id,
        CreatedAt=now,
        UpdatedAt=now,
    )
    db.add(cls)
    db.flush()  # get ClassID
    return cls


def _get_term(db: Session, academic_year_id: int, term_number: int) -> Term:
    term = (
        db.query(Term)
        .filter(
            Term.AcademicYearID == academic_year_id,
            Term.TermNumber == term_number,
        )
        .first()
    )
    if term is None:
        raise HTTPException(
            status_code=404,
            detail=f"Term {term_number} not found for academic year {academic_year_id}. "
                   "Create the academic year first (it auto-creates both terms).",
        )
    return term


# ---------------------------------------------------------------------------
# POST /v2/academics/grade-setup
# ---------------------------------------------------------------------------

@router.post(
    "/grade-setup",
    response_model=GradeLevelSetupOut,
    status_code=status.HTTP_201_CREATED,
    summary="One-form: create grade level with subjects per term",
)
def grade_level_setup(
    body: GradeLevelSetupIn,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> GradeLevelSetupOut:
    """
    Set up a complete grade level in one request.

    1. Verifies the academic year exists.
    2. Creates (or reuses) the Class row for this grade level.
    3. For each term in the request, assigns the listed subjects as
       SubjectOffering rows (skips duplicates silently).

    **Example body:**
    ```json
    {
      "academic_year_id": 1,
      "grade_level": 7,
      "class_name": "Grade 7",
      "terms": [
        {
          "term_number": 1,
          "teacher_id": 5,
          "subject_ids": [1, 2, 3]
        },
        {
          "term_number": 2,
          "teacher_id": 5,
          "subject_ids": [4, 5, 6]
        }
      ]
    }
    ```
    """
    # 1. Verify academic year
    ay = db.query(AcademicYear).filter(
        AcademicYear.AcademicYearID == body.academic_year_id
    ).first()
    if ay is None:
        raise HTTPException(status_code=404, detail="Academic year not found")

    # 2. Get or create the Class for this grade
    cls = _get_or_create_class(db, body.academic_year_id, body.grade_level, body.class_name)

    # 3. Process terms
    terms_out: list[TermSubjectsOut] = []
    now = datetime.now(timezone.utc)

    for term_in in body.terms:
        term = _get_term(db, body.academic_year_id, term_in.term_number)

        created = 0
        skipped = 0

        for subject_id in term_in.subject_ids:
            # Verify subject exists
            subj = db.query(Subject).filter(Subject.SubjectID == subject_id).first()
            if subj is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Subject {subject_id} not found",
                )

            # Skip if offering already exists
            exists = (
                db.query(SubjectOffering)
                .filter(
                    SubjectOffering.SubjectID == subject_id,
                    SubjectOffering.TermID == term.TermID,
                    SubjectOffering.ClassID == cls.ClassID,
                )
                .first()
            )
            if exists:
                skipped += 1
                continue

            offering = SubjectOffering(
                SubjectID=subject_id,
                TermID=term.TermID,
                ClassID=cls.ClassID,
                TeacherID=term_in.teacher_id,
                IsActive=True,
                CreatedAt=now,
                UpdatedAt=now,
            )
            db.add(offering)
            created += 1

        terms_out.append(
            TermSubjectsOut(
                term_id=term.TermID,
                term_name=term.TermName,
                term_number=term.TermNumber,
                offerings_created=created,
                offerings_skipped=skipped,
            )
        )

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Setup failed: {exc}") from exc

    db.refresh(cls)

    return GradeLevelSetupOut(
        class_id=cls.ClassID,
        class_name=cls.ClassName,
        grade_level=cls.GradeLevel,
        academic_year_id=cls.AcademicYearID,
        terms=terms_out,
    )


# ---------------------------------------------------------------------------
# GET /v2/academics/grade-levels
# ---------------------------------------------------------------------------

@router.get(
    "/grade-levels",
    summary="List distinct grade levels for an academic year",
)
def list_grade_levels(
    academic_year_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> list[dict]:
    """
    Returns distinct grade levels (with their class IDs) for a given
    academic year – useful for populating the student enrollment dropdown.
    """
    rows = (
        db.query(Class)
        .filter(Class.AcademicYearID == academic_year_id)
        .order_by(Class.GradeLevel)
        .all()
    )
    return [
        {
            "class_id": r.ClassID,
            "class_name": r.ClassName,
            "grade_level": r.GradeLevel,
            "academic_year_id": r.AcademicYearID,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# GET /v2/academics/grade-levels/{grade_level}/subjects
# ---------------------------------------------------------------------------

@router.get(
    "/grade-levels/{grade_level}/subjects",
    response_model=GradeLevelSubjectsOut,
    summary="Preview all subjects for a grade level (across both terms)",
)
def get_grade_level_subjects(
    grade_level: int,
    academic_year_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> GradeLevelSubjectsOut:
    """
    Returns all subjects assigned to the given grade level + academic year,
    split by term. Used to preview what a student will be enrolled in
    before calling /enroll-by-grade.
    """
    cls = (
        db.query(Class)
        .filter(
            Class.AcademicYearID == academic_year_id,
            Class.GradeLevel == grade_level,
        )
        .first()
    )
    if cls is None:
        raise HTTPException(
            status_code=404,
            detail=f"Grade level {grade_level} not found for academic year {academic_year_id}. "
                   "Run grade-setup first.",
        )

    # Get all term IDs for this year
    term_ids = [
        t.TermID
        for t in db.query(Term).filter(Term.AcademicYearID == academic_year_id).all()
    ]

    offerings = (
        db.query(SubjectOffering)
        .filter(
            SubjectOffering.ClassID == cls.ClassID,
            SubjectOffering.TermID.in_(term_ids),
            SubjectOffering.IsActive == True,
        )
        .all()
    )

    subjects_out: list[SubjectSummary] = []
    for o in offerings:
        subjects_out.append(
            SubjectSummary(
                subject_id=o.SubjectID,
                subject_code=o.Subject.SubjectCode if o.Subject else "",
                subject_name=o.Subject.SubjectName if o.Subject else "",
                term_number=o.Term.TermNumber if o.Term else 0,
                term_name=o.Term.TermName if o.Term else "",
                offering_id=o.OfferingID,
            )
        )

    return GradeLevelSubjectsOut(
        class_id=cls.ClassID,
        class_name=cls.ClassName,
        grade_level=cls.GradeLevel,
        academic_year_id=cls.AcademicYearID,
        subjects=subjects_out,
    )


# ---------------------------------------------------------------------------
# POST /v2/academics/enroll-by-grade
# ---------------------------------------------------------------------------

@router.post(
    "/enroll-by-grade",
    response_model=GradeLevelEnrollOut,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll student by grade level (auto-gets subjects)",
)
def enroll_by_grade(
    body: GradeLevelEnrollIn,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> GradeLevelEnrollOut:
    """
    Enroll a student by simply choosing their grade level.

    - Looks up the Class for the given grade_level + academic_year_id.
    - Creates an Enrollment record for that class.
    - Returns a summary of all subjects the student is now enrolled in
      (pulled from SubjectOfferings for that class).

    **The student gets all subjects for that grade level automatically.**
    No need to manually link subjects – they're inherited from the grade setup.
    """
    # 1. Find the class for this grade level
    cls = (
        db.query(Class)
        .filter(
            Class.AcademicYearID == body.academic_year_id,
            Class.GradeLevel == body.grade_level,
        )
        .first()
    )
    if cls is None:
        raise HTTPException(
            status_code=404,
            detail=f"Grade level {body.grade_level} not found for academic year {body.academic_year_id}. "
                   "Use POST /v2/academics/grade-setup first.",
        )

    # 2. Check for duplicate enrollment
    existing_enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.StudentID == body.student_id,
            Enrollment.ClassID == cls.ClassID,
            Enrollment.AcademicYearID == body.academic_year_id,
        )
        .first()
    )
    if existing_enrollment:
        raise HTTPException(
            status_code=409,
            detail=f"Student {body.student_id} is already enrolled in grade level "
                   f"{body.grade_level} for this academic year "
                   f"(enrollment_id={existing_enrollment.EnrollmentID}).",
        )

    # 3. Create enrollment
    now = datetime.now(timezone.utc)
    enrollment = Enrollment(
        StudentID=body.student_id,
        ClassID=cls.ClassID,
        AcademicYearID=body.academic_year_id,
        EnrollmentDate=body.enrollment_date,
        Status=body.status,
        CreatedAt=now,
        UpdatedAt=now,
    )
    db.add(enrollment)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Enrollment failed: {exc}") from exc
    db.refresh(enrollment)

    # 4. Build subjects summary (from SubjectOfferings)
    term_ids = [
        t.TermID
        for t in db.query(Term).filter(Term.AcademicYearID == body.academic_year_id).all()
    ]

    offerings = (
        db.query(SubjectOffering)
        .filter(
            SubjectOffering.ClassID == cls.ClassID,
            SubjectOffering.TermID.in_(term_ids),
            SubjectOffering.IsActive == True,
        )
        .all()
    )

    # Group by term
    terms_map: dict[int, TermSubjectsOut] = {}
    for o in offerings:
        t = o.Term
        if t and t.TermID not in terms_map:
            terms_map[t.TermID] = TermSubjectsOut(
                term_id=t.TermID,
                term_name=t.TermName,
                term_number=t.TermNumber,
                offerings_created=0,
                offerings_skipped=0,
            )
        if t:
            terms_map[t.TermID].offerings_created += 1

    return GradeLevelEnrollOut(
        student_id=enrollment.StudentID,
        class_id=cls.ClassID,
        class_name=cls.ClassName,
        enrollment_id=enrollment.EnrollmentID,
        grade_level=cls.GradeLevel,
        academic_year_id=body.academic_year_id,
        total_subjects=len(offerings),
        terms_summary=list(terms_map.values()),
    )
