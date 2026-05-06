from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import require_student
from app.db.entities import (
    Assignment,
    AssignmentSubmission,
    Attendance,
    Class,
    ClassSubject,
    Enrollment,
    Grade,
    Subject,
    GradeScale,
)
from app.db.session import get_db
from app.schemas.assignments import AssignmentOut, AssignmentSubmissionOut
from app.schemas.grades import GradeOut
from app.schemas.attendance import AttendanceOut
from app.schemas.academics import SubjectOut, ClassOut

router = APIRouter(prefix="/student", tags=["Student"])


@router.get("/dashboard")
def get_student_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    # 1. Stats
    # GPA - simple average of marks percentage for now, or use GradeScale if available
    grades = db.query(Grade).filter(Grade.StudentID == current_user.UserID).all()
    avg_percentage = sum([g.Percentage for g in grades]) / len(grades) if grades else 0
    # Convert percentage to 4.0 scale (rough estimation)
    gpa = round((avg_percentage / 100) * 4, 2)

    # Attendance
    attendance_records = db.query(Attendance).filter(Attendance.StudentID == current_user.UserID).all()
    present_count = len([a for a in attendance_records if a.Status == "Present"])
    attendance_pct = round((present_count / len(attendance_records)) * 100) if attendance_records else 0

    # Subjects
    enrollments = db.query(Enrollment).filter(
        Enrollment.StudentID == current_user.UserID,
        Enrollment.Status == "Active"
    ).all()
    class_ids = [e.ClassID for e in enrollments]
    total_subjects = db.query(ClassSubject).filter(ClassSubject.ClassID.in_(class_ids)).distinct(ClassSubject.SubjectID).count()

    # Pending Assignments
    # Get all assignments for student's classes
    class_subject_ids = [cs.ClassSubjectID for cs in db.query(ClassSubject).filter(ClassSubject.ClassID.in_(class_ids)).all()]
    all_assignments = db.query(Assignment).filter(Assignment.ClassSubjectID.in_(class_subject_ids)).all()
    
    # Get student submissions
    submissions = db.query(AssignmentSubmission).filter(AssignmentSubmission.StudentID == current_user.UserID).all()
    submitted_assignment_ids = [s.AssignmentID for s in submissions]
    
    pending_assignments = [a for a in all_assignments if a.AssignmentID not in submitted_assignment_ids]
    pending_count = len(pending_assignments)

    # 2. Recent Assignments (latest 5)
    recent_assignments = []
    for a in pending_assignments[:5]:
        # Get subject name
        cs = db.query(ClassSubject).filter(ClassSubject.ClassSubjectID == a.ClassSubjectID).first()
        subject_name = cs.Subject.SubjectName if cs and cs.Subject else "Unknown"
        recent_assignments.append({
            "id": a.AssignmentID,
            "title": a.Title,
            "subject": subject_name,
            "due_date": a.DueDate
        })

    return {
        "stats": {
            "gpa": gpa,
            "attendance": attendance_pct,
            "subjects": total_subjects,
            "pending": pending_count
        },
        "recent_assignments": recent_assignments
    }


@router.get("/my-classes", response_model=List[ClassOut])
def get_my_classes(
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    enrollments = db.query(Enrollment).filter(
        Enrollment.StudentID == current_user.UserID,
        Enrollment.Status == "Active"
    ).all()
    
    class_ids = [e.ClassID for e in enrollments]
    rows = db.query(Class).filter(Class.ClassID.in_(class_ids)).all()
    return [
        ClassOut(
            class_id=r.ClassID,
            class_name=r.ClassName,
            grade_level=r.GradeLevel,
            section=r.Section,
            academic_year_id=r.AcademicYearID,
            class_teacher_id=r.ClassTeacherID,
            max_capacity=r.MaxCapacity,
            room_number=r.RoomNumber
        ) for r in rows
    ]


@router.get("/my-subjects")
def get_my_subjects(
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    enrollments = db.query(Enrollment).filter(
        Enrollment.StudentID == current_user.UserID,
        Enrollment.Status == "Active"
    ).all()
    
    class_ids = [e.ClassID for e in enrollments]
    class_subjects = db.query(ClassSubject).filter(ClassSubject.ClassID.in_(class_ids)).all()
    
    result = []
    for cs in class_subjects:
        result.append({
            "class_subject_id": cs.ClassSubjectID,
            "subject_id": cs.SubjectID,
            "subject_code": cs.Subject.SubjectCode,
            "subject_name": cs.Subject.SubjectName,
            "teacher_name": f"{cs.TeacherProfile.User.FirstName} {cs.TeacherProfile.User.LastName}" if cs.TeacherProfile and cs.TeacherProfile.User else "Unknown",
            "description": cs.Subject.Description,
            "credit_hours": cs.Subject.CreditHours,
            "is_elective": cs.Subject.IsElective
        })
    
    return result


@router.get("/assignments", response_model=List[AssignmentOut])
def list_my_assignments(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    enrollments = db.query(Enrollment).filter(
        Enrollment.StudentID == current_user.UserID,
        Enrollment.Status == "Active"
    ).all()
    
    class_ids = [e.ClassID for e in enrollments]
    class_subjects = db.query(ClassSubject).filter(ClassSubject.ClassID.in_(class_ids)).all()
    class_subject_ids = [cs.ClassSubjectID for cs in class_subjects]
    
    assignments = db.query(Assignment).filter(
        Assignment.ClassSubjectID.in_(class_subject_ids)
    ).offset(skip).limit(limit).all()
    
    return [
        AssignmentOut(
            assignment_id=a.AssignmentID,
            class_subject_id=a.ClassSubjectID,
            title=a.Title,
            description=a.Description,
            due_date=a.DueDate,
            file_path=a.FilePath,
            max_marks=a.MaxMarks,
            created_by_id=a.CreatedByID,
            created_at=a.CreatedAt,
            updated_at=a.UpdatedAt
        ) for a in assignments
    ]


@router.get("/assignments/{assignment_id}/download")
def download_assignment_file(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    # 1. Verify assignment exists
    assignment = db.query(Assignment).filter(Assignment.AssignmentID == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if not assignment.FilePath:
        raise HTTPException(status_code=404, detail="No file attached to this assignment")

    # 2. Verify student is enrolled in the class for this assignment
    enrollment = db.query(Enrollment).join(ClassSubject, Enrollment.ClassID == ClassSubject.ClassID).filter(
        Enrollment.StudentID == current_user.UserID,
        ClassSubject.ClassSubjectID == assignment.ClassSubjectID,
        Enrollment.Status == "Active"
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not authorized to access this assignment")

    import os
    if not os.path.exists(assignment.FilePath):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=assignment.FilePath,
        filename=os.path.basename(assignment.FilePath),
        media_type='application/pdf'
    )


@router.get("/submissions/{submission_id}/download")
def download_my_submission_file(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    # 1. Verify submission exists and belongs to the student
    submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.SubmissionID == submission_id,
        AssignmentSubmission.StudentID == current_user.UserID
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    if not submission.FilePath:
        raise HTTPException(status_code=404, detail="No file attached to this submission")

    import os
    if not os.path.exists(submission.FilePath):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=submission.FilePath,
        filename=os.path.basename(submission.FilePath),
        media_type='application/pdf'
    )


@router.post("/assignments/{assignment_id}/submit", response_model=AssignmentSubmissionOut)
def submit_assignment(
    assignment_id: int,
    comments: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    # Verify assignment exists
    assignment = db.query(Assignment).filter(Assignment.AssignmentID == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    import os, shutil
    upload_dir = f"uploads/assignments"
    os.makedirs(upload_dir, exist_ok=True)
    safe_filename = f"{current_user.UserID}_{assignment_id}_{file.filename}"
    file_path = f"{upload_dir}/{safe_filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    now = datetime.now(timezone.utc)
    submission = AssignmentSubmission(
        AssignmentID=assignment_id,
        StudentID=current_user.UserID,
        SubmittedAt=now,
        FilePath=file_path,
        Comments=comments,
        Status="Submitted",
        CreatedAt=now,
        UpdatedAt=now
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    
    return AssignmentSubmissionOut(
        submission_id=submission.SubmissionID,
        assignment_id=submission.AssignmentID,
        student_id=submission.StudentID,
        submitted_at=submission.SubmittedAt,
        file_path=submission.FilePath,
        comments=submission.Comments,
        status=submission.Status,
        created_at=submission.CreatedAt,
        updated_at=submission.UpdatedAt
    )


@router.get("/grades", response_model=List[GradeOut])
def get_my_grades(
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    grades = db.query(Grade).filter(Grade.StudentID == current_user.UserID).all()
    return [
        GradeOut(
            grade_id=g.GradeID,
            student_id=g.StudentID,
            class_subject_id=g.ClassSubjectID,
            academic_year_id=g.AcademicYearID,
            assignment_id=g.AssignmentID,
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


@router.get("/attendance", response_model=List[AttendanceOut])
def get_my_attendance(
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    attendance = db.query(Attendance).filter(Attendance.StudentID == current_user.UserID).all()
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
