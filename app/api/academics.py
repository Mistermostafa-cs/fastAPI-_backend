from datetime import datetime, timezone, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.entities import AcademicYear, Class, ClassSubject, Enrollment, Subject
from app.db.session import get_db
from app.schemas.academics import (
    AcademicYearIn,
    AcademicYearOut,
    ClassIn,
    ClassOut,
    ClassSubjectIn,
    ClassSubjectOut,
    EnrollmentIn,
    EnrollmentOut,
    SubjectIn,
    SubjectOut,
)

router = APIRouter(prefix="/academics", tags=["Academics"])


@router.get("/academic-years", response_model=list[AcademicYearOut])
def list_academic_years(db: Session = Depends(get_db), _=Depends(require_admin)) -> list[AcademicYearOut]:
    rows = db.query(AcademicYear).order_by(AcademicYear.AcademicYearID.desc()).all()
    return [
        AcademicYearOut(
            academic_year_id=r.AcademicYearID,
            year_label=r.YearLabel,
            start_date=r.StartDate,
            end_date=r.EndDate,
            is_current=r.IsCurrent,
            created_at=r.CreatedAt,
        )
        for r in rows
    ]


@router.post("/academic-years", response_model=AcademicYearOut, status_code=status.HTTP_201_CREATED)
def create_academic_year(
    year_label: str = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
    is_current: bool = Form(False),
    db: Session = Depends(get_db),
    _=Depends(require_admin)
) -> AcademicYearOut:
    now = datetime.now(timezone.utc)
    row = AcademicYear(
        YearLabel=year_label,
        StartDate=start_date,
        EndDate=end_date,
        IsCurrent=is_current,
        CreatedAt=now,
        UpdatedAt=now,
    )
    db.add(row)
    db.flush()  # get AcademicYearID before auto-creating terms

    # ── Auto-create Term 1 & Term 2 for the new year ──────────────────────
    try:
        from app.services.term_offering_service import create_default_terms
        create_default_terms(db, row)
    except Exception:
        pass  # best-effort, don't block year creation
    # ─────────────────────────────────────────────────────────────────────

    db.commit()
    db.refresh(row)
    return AcademicYearOut(
        academic_year_id=row.AcademicYearID,
        year_label=row.YearLabel,
        start_date=row.StartDate,
        end_date=row.EndDate,
        is_current=row.IsCurrent,
        created_at=row.CreatedAt,
    )


@router.get("/classes", response_model=list[ClassOut])
def list_classes(db: Session = Depends(get_db), _=Depends(require_admin)) -> list[ClassOut]:
    rows = db.query(Class).order_by(Class.ClassID.desc()).all()
    return [
        ClassOut(
            class_id=r.ClassID,
            class_name=r.ClassName,
            grade_level=r.GradeLevel,
            section=r.Section,
            academic_year_id=r.AcademicYearID,
            class_teacher_id=r.ClassTeacherID,
            max_capacity=r.MaxCapacity,
            room_number=r.RoomNumber,
        )
        for r in rows
    ]


@router.post("/classes", response_model=ClassOut, status_code=status.HTTP_201_CREATED)
def create_class(
    class_name: str = Form(...),
    grade_level: int = Form(...),
    section: Optional[str] = Form(None),
    academic_year_id: int = Form(...),
    class_teacher_id: Optional[int] = Form(None),
    max_capacity: Optional[int] = Form(None),
    room_number: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin)
) -> ClassOut:
    now = datetime.now(timezone.utc)
    row = Class(
        ClassName=class_name,
        GradeLevel=grade_level,
        Section=section,
        AcademicYearID=academic_year_id,
        ClassTeacherID=class_teacher_id,
        MaxCapacity=max_capacity,
        RoomNumber=room_number,
        CreatedAt=now,
        UpdatedAt=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ClassOut(
        class_id=row.ClassID,
        class_name=row.ClassName,
        grade_level=row.GradeLevel,
        section=row.Section,
        academic_year_id=row.AcademicYearID,
        class_teacher_id=row.ClassTeacherID,
        max_capacity=row.MaxCapacity,
        room_number=row.RoomNumber,
    )


@router.get("/subjects", response_model=list[SubjectOut])
def list_subjects(db: Session = Depends(get_db), _=Depends(require_admin)) -> list[SubjectOut]:
    rows = db.query(Subject).order_by(Subject.SubjectID.desc()).all()
    return [
        SubjectOut(
            subject_id=r.SubjectID,
            subject_code=r.SubjectCode,
            subject_name=r.SubjectName,
            description=r.Description,
            credit_hours=r.CreditHours,
            is_elective=r.IsElective,
        )
        for r in rows
    ]


@router.post("/subjects", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(
    subject_code: str = Form(...),
    subject_name: str = Form(...),
    description: Optional[str] = Form(None),
    credit_hours: Optional[int] = Form(None),
    is_elective: bool = Form(False),
    db: Session = Depends(get_db),
    _=Depends(require_admin)
) -> SubjectOut:
    now = datetime.now(timezone.utc)
    row = Subject(
        SubjectCode=subject_code,
        SubjectName=subject_name,
        Description=description,
        CreditHours=credit_hours,
        IsElective=is_elective,
        CreatedAt=now,
        UpdatedAt=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return SubjectOut(
        subject_id=row.SubjectID,
        subject_code=row.SubjectCode,
        subject_name=row.SubjectName,
        description=row.Description,
        credit_hours=row.CreditHours,
        is_elective=row.IsElective,
    )


@router.get("/class-subjects", response_model=list[ClassSubjectOut])
def list_class_subjects(db: Session = Depends(get_db), _=Depends(require_admin)) -> list[ClassSubjectOut]:
    rows = db.query(ClassSubject).order_by(ClassSubject.ClassSubjectID.desc()).all()
    return [
        ClassSubjectOut(
            class_subject_id=r.ClassSubjectID,
            class_id=r.ClassID,
            subject_id=r.SubjectID,
            teacher_id=r.TeacherID,
            academic_year_id=r.AcademicYearID,
        )
        for r in rows
    ]


@router.post("/class-subjects", response_model=ClassSubjectOut, status_code=status.HTTP_201_CREATED)
def create_class_subject(
    class_id: int = Form(...),
    subject_id: int = Form(...),
    teacher_id: int = Form(...),
    academic_year_id: int = Form(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> ClassSubjectOut:
    now = datetime.now(timezone.utc)
    row = ClassSubject(
        ClassID=class_id,
        SubjectID=subject_id,
        TeacherID=teacher_id,
        AcademicYearID=academic_year_id,
        CreatedAt=now,
        UpdatedAt=now,
    )
    db.add(row)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create class subject mapping") from exc
    db.refresh(row)
    return ClassSubjectOut(
        class_subject_id=row.ClassSubjectID,
        class_id=row.ClassID,
        subject_id=row.SubjectID,
        teacher_id=row.TeacherID,
        academic_year_id=row.AcademicYearID,
    )


@router.get("/enrollments", response_model=list[EnrollmentOut])
def list_enrollments(db: Session = Depends(get_db), _=Depends(require_admin)) -> list[EnrollmentOut]:
    rows = db.query(Enrollment).order_by(Enrollment.EnrollmentID.desc()).all()
    return [
        EnrollmentOut(
            enrollment_id=r.EnrollmentID,
            student_id=r.StudentID,
            class_id=r.ClassID,
            academic_year_id=r.AcademicYearID,
            enrollment_date=r.EnrollmentDate,
            status=r.Status,
        )
        for r in rows
    ]


@router.post("/enrollments", response_model=EnrollmentOut, status_code=status.HTTP_201_CREATED)
def create_enrollment(
    student_id: int = Form(...),
    class_id: int = Form(...),
    academic_year_id: int = Form(...),
    enrollment_date: date = Form(...),
    status: str = Form("Active"),
    db: Session = Depends(get_db),
    _=Depends(require_admin)
) -> EnrollmentOut:
    now = datetime.now(timezone.utc)
    row = Enrollment(
        StudentID=student_id,
        ClassID=class_id,
        AcademicYearID=academic_year_id,
        EnrollmentDate=enrollment_date,
        Status=status,
        CreatedAt=now,
        UpdatedAt=now,
    )
    db.add(row)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not create enrollment") from exc
    db.refresh(row)
    return EnrollmentOut(
        enrollment_id=row.EnrollmentID,
        student_id=row.StudentID,
        class_id=row.ClassID,
        academic_year_id=row.AcademicYearID,
        enrollment_date=row.EnrollmentDate,
        status=row.Status,
    )
