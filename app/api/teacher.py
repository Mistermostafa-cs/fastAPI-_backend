from datetime import datetime, timezone
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.deps import require_teacher
from app.db.entities import (
    Exam,
    Question,
    Option,
    Attendance,
    Grade,
    ClassSubject,
    Enrollment,
    StudentProfile,
    Class,
    Subject,
    Assignment,
    AssignmentSubmission,
)
from app.db.session import get_db
from app.schemas.exams import ExamOut, ExamIn, QuestionIn
from app.schemas.attendance import AttendanceOut, AttendanceIn
from app.schemas.grades import GradeOut, GradeIn
from app.schemas.academics import ClassOut, SubjectOut

router = APIRouter(prefix="/teacher", tags=["Teacher"])

# --- Dashboard ---

@router.get("/dashboard")
def get_teacher_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(require_teacher)
):
    # Get all subjects taught by this teacher
    class_subjects = db.query(ClassSubject).filter(ClassSubject.TeacherID == current_user.UserID).all()
    
    total_classes = len(set([cs.ClassID for cs in class_subjects]))
    total_subjects = len(set([cs.SubjectID for cs in class_subjects]))
    
    # Get total students across all assigned classes
    class_ids = [cs.ClassID for cs in class_subjects]
    total_students = db.query(Enrollment).filter(Enrollment.ClassID.in_(class_ids), Enrollment.Status == "Active").count()
    
    # Get recent assignments and submission counts
    recent_assignments = db.query(Assignment).filter(
        Assignment.CreatedByID == current_user.UserID
    ).order_by(Assignment.CreatedAt.desc()).limit(5).all()
    
    assignments_data = []
    for a in recent_assignments:
        submission_count = db.query(AssignmentSubmission).filter(AssignmentSubmission.AssignmentID == a.AssignmentID).count()
        assignments_data.append({
            "id": a.AssignmentID,
            "title": a.Title,
            "due_date": a.DueDate,
            "submissions": submission_count
        })

    # Get total quizzes/exams created by this teacher
    total_quizzes = db.query(Exam).filter(Exam.CreatedByID == current_user.UserID).count()

    return {
        "stats": {
            "total_classes": total_classes,
            "total_subjects": total_subjects,
            "total_students": total_students,
            "total_quizzes": total_quizzes
        },
        "recent_assignments": assignments_data
    }

@router.get("/my-classes", response_model=List[ClassOut])
def get_teacher_classes(
    db: Session = Depends(get_db),
    current_user=Depends(require_teacher)
):
    class_subjects = db.query(ClassSubject).filter(ClassSubject.TeacherID == current_user.UserID).all()
    class_ids = [cs.ClassID for cs in class_subjects]
    classes = db.query(Class).filter(Class.ClassID.in_(class_ids)).all()
    
    return [
        ClassOut(
            class_id=c.ClassID,
            class_name=c.ClassName,
            grade_level=c.GradeLevel,
            section=c.Section,
            academic_year_id=c.AcademicYearID,
            class_teacher_id=c.ClassTeacherID,
            max_capacity=c.MaxCapacity,
            room_number=c.RoomNumber
        ) for c in classes
    ]

@router.get("/my-students")
def get_teacher_students(
    db: Session = Depends(get_db),
    current_user=Depends(require_teacher)
):
    # Get all students in classes taught by this teacher
    class_subjects = db.query(ClassSubject).filter(ClassSubject.TeacherID == current_user.UserID).all()
    class_ids = [cs.ClassID for cs in class_subjects]
    
    students = db.query(StudentProfile).join(Enrollment, StudentProfile.StudentID == Enrollment.StudentID).filter(
        Enrollment.ClassID.in_(class_ids),
        Enrollment.Status == "Active"
    ).all()
    
    result = []
    for s in students:
        # Get class name for this student
        enrollment = db.query(Enrollment).filter(
            Enrollment.StudentID == s.StudentID, 
            Enrollment.ClassID.in_(class_ids)
        ).first()
        class_obj = db.query(Class).filter(Class.ClassID == enrollment.ClassID).first() if enrollment else None
        
        # Calculate attendance (overall for simplicity)
        att_records = db.query(Attendance).filter(Attendance.StudentID == s.StudentID).all()
        present_count = len([a for a in att_records if a.Status == "Present"])
        att_pct = round((present_count / len(att_records)) * 100) if att_records else 0
        
        # Calculate avg grade (overall)
        grade_records = db.query(Grade).filter(Grade.StudentID == s.StudentID).all()
        percentages = [g.Percentage for g in grade_records if g.Percentage is not None]
        avg_g = round(float(sum(percentages)) / len(percentages)) if percentages else 0

        result.append({
            "student_id": s.StudentID,
            "roll_number": s.RollNumber,
            "full_name": f"{s.User.FirstName} {s.User.LastName}" if s.User else "Unknown",
            "class_name": class_obj.ClassName if class_obj else "Unknown",
            "grade_level": class_obj.GradeLevel if class_obj else "Unknown",
            "attendance_pct": att_pct,
            "avg_grade": avg_g
        })
    return result

# --- Attendance ---

@router.post("/attendance", response_model=List[AttendanceOut])
def mark_attendance(
    attendance_data: List[AttendanceIn],
    db: Session = Depends(get_db),
    current_user=Depends(require_teacher)
):
    now = datetime.now(timezone.utc)
    results = []
    
    for item in attendance_data:
        # Check if attendance already exists for this student on this date/subject
        existing = db.query(Attendance).filter(
            Attendance.StudentID == item.student_id,
            Attendance.ClassSubjectID == item.class_subject_id,
            Attendance.AttendanceDate == item.attendance_date
        ).first()
        
        if existing:
            existing.Status = item.status
            existing.Remarks = item.remarks
            existing.MarkedByID = current_user.UserID
            existing.UpdatedAt = now
            db.add(existing)
            results.append(existing)
        else:
            new_attendance = Attendance(
                StudentID=item.student_id,
                ClassSubjectID=item.class_subject_id,
                AttendanceDate=item.attendance_date,
                Status=item.status,
                Remarks=item.remarks,
                MarkedByID=current_user.UserID,
                CreatedAt=now,
                UpdatedAt=now
            )
            db.add(new_attendance)
            results.append(new_attendance)
            
    db.commit()
    for r in results: db.refresh(r)
    
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
        ) for a in results
    ]

# --- Grades ---

@router.post("/grades", response_model=List[GradeOut])
def enter_grades(
    grades_data: List[GradeIn],
    db: Session = Depends(get_db),
    current_user=Depends(require_teacher)
):
    now = datetime.now(timezone.utc)
    results = []
    
    for item in grades_data:
        existing = db.query(Grade).filter(
            Grade.StudentID == item.student_id,
            Grade.ClassSubjectID == item.class_subject_id,
            Grade.ExamID == item.exam_id
        ).first()
        
        percentage = (item.marks_obtained / item.total_marks) * 100 if item.total_marks > 0 else 0
        
        if existing:
            existing.MarksObtained = item.marks_obtained
            existing.TotalMarks = item.total_marks
            existing.Percentage = percentage
            existing.IsPassed = item.is_passed
            existing.Remarks = item.remarks
            existing.InputByID = current_user.UserID
            existing.UpdatedAt = now
            db.add(existing)
            results.append(existing)
        else:
            new_grade = Grade(
                StudentID=item.student_id,
                ClassSubjectID=item.class_subject_id,
                AcademicYearID=item.academic_year_id,
                ExamID=item.exam_id,
                MarksObtained=item.marks_obtained,
                TotalMarks=item.total_marks,
                Percentage=percentage,
                IsPassed=item.is_passed,
                GradeScaleID=item.grade_scale_id,
                Remarks=item.remarks,
                InputByID=current_user.UserID,
                CreatedAt=now,
                UpdatedAt=now
            )
            db.add(new_grade)
            results.append(new_grade)
            
    db.commit()
    for r in results: db.refresh(r)
    
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
        ) for g in results
    ]

@router.get("/assignments/{assignment_id}/submissions")
def get_assignment_submissions(
    assignment_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user=Depends(require_teacher)
):
    submissions = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.AssignmentID == assignment_id
    ).offset(skip).limit(limit).all()
    
    result = []
    for s in submissions:
        student = db.query(StudentProfile).filter(StudentProfile.UserID == s.StudentID).first()
        result.append({
            "submission_id": s.SubmissionID,
            "student_id": s.StudentID,
            "student_name": f"{student.User.FirstName} {student.User.LastName}" if student and student.User else "Unknown",
            "submitted_at": s.SubmittedAt,
            "file_path": s.FilePath,
            "comments": s.Comments,
            "status": s.Status,
            "marks_obtained": s.MarksObtained,
            "graded_at": s.GradedAt
        })
    return result

# --- Quizzes (MCQ) ---

@router.post("/quizzes", response_model=ExamOut)
def create_quiz(
    quiz_data: ExamIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_teacher)
):
    now = datetime.now(timezone.utc)
    
    # Create the Exam entry
    new_exam = Exam(
        ClassSubjectID=quiz_data.class_subject_id,
        ExamTypeID=quiz_data.exam_type_id,
        Title=quiz_data.title,
        Description=quiz_data.description,
        ExamDate=quiz_data.exam_date,
        DurationMinutes=quiz_data.duration_minutes,
        TotalMarks=quiz_data.total_marks,
        PassingMarks=quiz_data.passing_marks,
        IsOnline=True,
        CreatedByID=current_user.UserID,
        CreatedAt=now,
        UpdatedAt=now
    )
    db.add(new_exam)
    db.flush() # Get the ExamID
    
    # Add Questions and Options
    if quiz_data.questions:
        for idx, q_data in enumerate(quiz_data.questions):
            new_q = Question(
                ExamID=new_exam.ExamID,
                QuestionTypeID=q_data.question_type_id,
                QuestionText=q_data.question_text,
                QuestionOrder=idx + 1,
                Marks=q_data.marks,
                DifficultyLevel=q_data.difficulty_level,
                Explanation=q_data.explanation,
                CreatedAt=now,
                UpdatedAt=now
            )
            db.add(new_q)
            db.flush()
            
            if q_data.options:
                for o_idx, o_data in enumerate(q_data.options):
                    new_o = Option(
                        QuestionID=new_q.QuestionID,
                        OptionText=o_data.option_text,
                        IsCorrect=o_data.is_correct,
                        OptionOrder=o_idx + 1,
                        CreatedAt=now
                    )
                    db.add(new_o)
                    
    db.commit()
    db.refresh(new_exam)
    
    return ExamOut(
        exam_id=new_exam.ExamID,
        class_subject_id=new_exam.ClassSubjectID,
        exam_type_id=new_exam.ExamTypeID,
        title=new_exam.Title,
        description=new_exam.Description,
        exam_date=new_exam.ExamDate,
        duration_minutes=new_exam.DurationMinutes,
        total_marks=new_exam.TotalMarks,
        passing_marks=new_exam.PassingMarks,
        is_online=new_exam.IsOnline,
        created_by_id=new_exam.CreatedByID,
        created_at=new_exam.CreatedAt,
        updated_at=new_exam.UpdatedAt
    )
