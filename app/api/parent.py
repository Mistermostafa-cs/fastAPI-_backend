from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_parent
from app.db.entities import (
    ParentStudentLink,
    StudentProfile,
    Grade,
    Attendance,
    User,
    Enrollment,
    Class,
)
from app.db.session import get_db
from app.schemas.grades import GradeOut
from app.schemas.attendance import AttendanceOut
from pydantic import BaseModel

router = APIRouter(prefix="/parent", tags=["Parent"])

class ChildOut(BaseModel):
    student_id: int
    first_name: str
    last_name: str
    full_name: str
    class_name: str | None = None

    class Config:
        from_attributes = True

@router.get("/my-children", response_model=List[ChildOut])
def get_my_children(
    db: Session = Depends(get_db),
    current_user=Depends(require_parent)
):
    # Find children linked to this parent
    links = db.query(ParentStudentLink).filter(ParentStudentLink.ParentID == current_user.UserID).all()
    student_ids = [link.StudentID for link in links]
    
    students = db.query(StudentProfile).filter(StudentProfile.StudentID.in_(student_ids)).all()
    
    result = []
    for s in students:
        user = db.query(User).filter(User.UserID == s.StudentID).first()
        enrollment = db.query(Enrollment).filter(
            Enrollment.StudentID == s.StudentID,
            Enrollment.Status == "Active"
        ).first()
        class_obj = db.query(Class).filter(Class.ClassID == enrollment.ClassID).first() if enrollment else None
        class_name = class_obj.ClassName if class_obj else None
        if user:
            result.append(
                ChildOut(
                    student_id=s.StudentID,
                    first_name=user.FirstName,
                    last_name=user.LastName,
                    full_name=f"{user.FirstName} {user.LastName}",
                    class_name=class_name
                )
            )
    return result

@router.get("/children/{student_id}/grades", response_model=List[GradeOut])
def get_child_grades(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_parent)
):
    # Verify link
    link = db.query(ParentStudentLink).filter(
        ParentStudentLink.ParentID == current_user.UserID,
        ParentStudentLink.StudentID == student_id
    ).first()
    
    if not link:
        raise HTTPException(status_code=403, detail="Not authorized to view this student's grades")
        
    grades = db.query(Grade).filter(Grade.StudentID == student_id).all()
    return [
        GradeOut(
            grade_id=g.GradeID,
            student_id=g.StudentID,
            class_subject_id=g.ClassSubjectID,
            academic_year_id=g.AcademicYearID,
            exam_id=g.ExamID,
            marks_obtained=g.MarksObtained,
            total_marks=g.TotalMarks,
            percentage=g.Percentage,
            is_passed=g.IsPassed,
            grade_scale_id=g.GradeScaleID,
            remarks=g.Remarks,
            input_by_id=g.InputByID,
            created_at=g.CreatedAt,
            updated_at=g.UpdatedAt
        ) for g in grades
    ]

@router.get("/children/{student_id}/attendance", response_model=List[AttendanceOut])
def get_child_attendance(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_parent)
):
    # Verify link
    link = db.query(ParentStudentLink).filter(
        ParentStudentLink.ParentID == current_user.UserID,
        ParentStudentLink.StudentID == student_id
    ).first()
    
    if not link:
        raise HTTPException(status_code=403, detail="Not authorized to view this student's attendance")
        
    attendance = db.query(Attendance).filter(Attendance.StudentID == student_id).all()
    return [
        AttendanceOut(
            attendance_id=a.AttendanceID,
            student_id=a.StudentID,
            class_subject_id=a.ClassSubjectID,
            attendance_date=a.AttendanceDate,
            status=a.Status,
            remarks=a.Remarks,
            marked_by_id=a.MarkedByID,
            created_at=a.CreatedAt,
            updated_at=a.UpdatedAt
        ) for a in attendance
    ]
