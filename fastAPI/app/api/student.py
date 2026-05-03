from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.api.deps import require_student
from app.db.entities import (
    Assignment,
    AssignmentSubmission,
    Attendance,
    Class,
    ClassSubject,
    Enrollment,
    Exam,
    ExamSession,
    Grade,
    StudentAnswer,
    Question,
    Option,
    Subject,
    GradeScale,
)
from app.db.session import get_db
from app.schemas.assignments import AssignmentOut, AssignmentSubmissionOut
from app.schemas.exams import ExamOut, ExamSessionOut, ExamSubmissionIn, QuestionOut, OptionOut
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


@router.get("/exams/{exam_id}/questions", response_model=List[QuestionOut])
def get_exam_questions(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    # Verify student is enrolled in the class that has this exam
    exam = db.query(Exam).filter(Exam.ExamID == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    enrollment = db.query(Enrollment).join(ClassSubject, Enrollment.ClassID == ClassSubject.ClassID).filter(
        Enrollment.StudentID == current_user.UserID,
        ClassSubject.ClassSubjectID == exam.ClassSubjectID
    ).first()
    
    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not enrolled in this course")

    questions = db.query(Question).filter(Question.ExamID == exam_id).order_by(Question.QuestionOrder).all()
    
    result = []
    for q in questions:
        options = [
            OptionOut(
                option_id=o.OptionID,
                question_id=o.QuestionID,
                option_text=o.OptionText,
                is_correct=False, # Don't send correct answers to student!
                option_order=o.OptionOrder
            ) for o in q.Options
        ]
        result.append(
            QuestionOut(
                question_id=q.QuestionID,
                exam_id=q.ExamID,
                question_type_id=q.QuestionTypeID,
                question_text=q.QuestionText,
                question_order=q.QuestionOrder,
                marks=q.Marks,
                difficulty_level=q.DifficultyLevel,
                explanation=None, # Don't send explanation before submission
                options=options
            )
        )
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
            max_marks=a.MaxMarks,
            created_by_id=a.CreatedByID,
            created_at=a.CreatedAt,
            updated_at=a.UpdatedAt
        ) for a in assignments
    ]


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


@router.get("/exams", response_model=List[ExamOut])
def list_my_exams(
    class_subject_id: int = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    enrollments = db.query(Enrollment).filter(
        Enrollment.StudentID == current_user.UserID,
        Enrollment.Status == "Active"
    ).all()
    
    class_ids = [e.ClassID for e in enrollments]
    class_subjects_query = db.query(ClassSubject).filter(ClassSubject.ClassID.in_(class_ids))
    
    if class_subject_id:
        class_subjects_query = class_subjects_query.filter(ClassSubject.ClassSubjectID == class_subject_id)
        
    class_subjects = class_subjects_query.all()
    class_subject_ids = [cs.ClassSubjectID for cs in class_subjects]
    
    exams = db.query(Exam).filter(
        Exam.ClassSubjectID.in_(class_subject_ids),
        Exam.IsOnline == True
    ).all()
    
    return [
        ExamOut(
            exam_id=e.ExamID,
            class_subject_id=e.ClassSubjectID,
            exam_type_id=e.ExamTypeID,
            title=e.Title,
            description=e.Description,
            exam_date=e.ExamDate,
            duration_minutes=e.DurationMinutes,
            total_marks=e.TotalMarks,
            passing_marks=e.PassingMarks,
            is_online=e.IsOnline,
            created_by_id=e.CreatedByID,
            created_at=e.CreatedAt,
            updated_at=e.UpdatedAt
        ) for e in exams
    ]


@router.post("/exams/{exam_id}/start", response_model=ExamSessionOut)
def start_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    exam = db.query(Exam).filter(Exam.ExamID == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Check if session already exists
    existing_session = db.query(ExamSession).filter(
        ExamSession.ExamID == exam_id,
        ExamSession.StudentID == current_user.UserID,
        ExamSession.Status == "InProgress"
    ).first()
    
    if existing_session:
        return ExamSessionOut(
            session_id=existing_session.SessionID,
            exam_id=existing_session.ExamID,
            student_id=existing_session.StudentID,
            started_at=existing_session.StartedAt,
            status=existing_session.Status,
            created_at=existing_session.CreatedAt,
            updated_at=existing_session.UpdatedAt
        )

    now = datetime.now(timezone.utc)
    session = ExamSession(
        ExamID=exam_id,
        StudentID=current_user.UserID,
        StartedAt=now,
        Status="InProgress",
        CreatedAt=now,
        UpdatedAt=now
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return ExamSessionOut(
        session_id=session.SessionID,
        exam_id=session.ExamID,
        student_id=session.StudentID,
        started_at=session.StartedAt,
        status=session.Status,
        created_at=session.CreatedAt,
        updated_at=session.UpdatedAt
    )


@router.post("/exams/submit")
def submit_exam(
    payload: ExamSubmissionIn,
    db: Session = Depends(get_db),
    current_user=Depends(require_student)
):
    session = db.query(ExamSession).filter(
        ExamSession.SessionID == payload.session_id,
        ExamSession.StudentID == current_user.UserID,
        ExamSession.Status == "InProgress"
    ).first()
    
    if not session:
        raise HTTPException(status_code=400, detail="Invalid session")
    
    now = datetime.now(timezone.utc)
    total_score = 0
    
    for ans in payload.answers:
        question = db.query(Question).filter(Question.QuestionID == ans.question_id).first()
        if not question:
            continue
            
        is_correct = False
        if ans.selected_option_id:
            option = db.query(Option).filter(
                Option.OptionID == ans.selected_option_id,
                Option.QuestionID == ans.question_id
            ).first()
            if option and option.IsCorrect:
                is_correct = True
                total_score += question.Marks
        
        student_answer = StudentAnswer(
            SessionID=session.SessionID,
            QuestionID=ans.question_id,
            SelectedOptionID=ans.selected_option_id,
            AnswerText=ans.answer_text,
            IsCorrect=is_correct,
            MarksAwarded=question.Marks if is_correct else 0,
            CreatedAt=now,
            UpdatedAt=now
        )
        db.add(student_answer)
    
    session.SubmittedAt = now
    session.TotalScore = total_score
    session.Status = "Submitted"
    session.IsPassed = total_score >= session.Exam.PassingMarks
    session.UpdatedAt = now
    
    db.commit()
    return {"message": "Exam submitted successfully", "score": total_score}


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
