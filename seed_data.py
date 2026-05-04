from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from app.db.session import SessionLocal, engine
from app.db.entities import (
    Base,
    Role, User, AdminProfile, TeacherProfile, StudentProfile, 
    ParentProfile, ParentStudentLink, AcademicYear, Class, 
    Subject, ClassSubject, Enrollment, Exam, Question, Option,
    ExamType, QuestionType
)
from app.core.security import hash_password

def seed_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 0. Metadata (ExamTypes, QuestionTypes)
        exam_types = [
            (1, "Quiz"),
            (2, "Midterm"),
            (3, "Final"),
            (4, "Class Test"),
            (5, "Annual"),
        ]
        for tid, name in exam_types:
            if not db.query(ExamType).filter(ExamType.ExamTypeID == tid).first():
                db.add(ExamType(ExamTypeID=tid, TypeName=name))
        
        q_types = [
            (1, "MultipleChoice"),
            (2, "Descriptive"),
            (3, "TrueFalse"),
            (4, "FillInBlank"),
        ]
        for tid, name in q_types:
            if not db.query(QuestionType).filter(QuestionType.QuestionTypeID == tid).first():
                db.add(QuestionType(QuestionTypeID=tid, TypeName=name))
        db.flush()

        # 1. Roles
        roles_data = [
            (1, "Admin", "Full system access"),
            (2, "Teacher", "Class & exam management"),
            (3, "Student", "Quiz, grades & homework"),
            (4, "Parent", "View & fee payments"),
        ]
        
        roles = {}
        for rid, name, desc in roles_data:
            role = db.query(Role).filter(Role.RoleID == rid).first()
            if not role:
                role = Role(RoleID=rid, RoleName=name, Description=desc)
                db.add(role)
                db.flush()
            roles[name] = role

        # 2. Academic Year
        ay = db.query(AcademicYear).filter(AcademicYear.YearLabel == "2025-2026").first()
        if not ay:
            ay = AcademicYear(
                YearLabel="2025-2026",
                StartDate=date(2025, 9, 1),
                EndDate=date(2026, 6, 30),
                IsCurrent=True
            )
            db.add(ay)
            db.flush()

        # 3. Teacher
        teacher_email = "teacher@school.com"
        teacher_user = db.query(User).filter(User.Email == teacher_email).first()
        if not teacher_user:
            teacher_user = User(
                RoleID=roles["Teacher"].RoleID,
                FirstName="John",
                LastName="Doe",
                Email=teacher_email,
                PasswordHash=hash_password("Teacher@123"),
                CreatedAt=datetime.now(timezone.utc),
                UpdatedAt=datetime.now(timezone.utc),
                IsActive=True
            )
            db.add(teacher_user)
            db.flush()
            
            teacher_profile = TeacherProfile(
                TeacherID=teacher_user.UserID,
                EmployeeCode="TCH001",
                Qualification="PhD in Mathematics",
                Specialization="Mathematics",
                JoiningDate=date(2020, 1, 1),
                Salary=Decimal("5000.00")
            )
            db.add(teacher_profile)

        # 4. Parent
        parent_email = "parent@home.com"
        parent_user = db.query(User).filter(User.Email == parent_email).first()
        if not parent_user:
            parent_user = User(
                RoleID=roles["Parent"].RoleID,
                FirstName="Robert",
                LastName="Smith",
                Email=parent_email,
                PasswordHash=hash_password("Parent@123"),
                CreatedAt=datetime.now(timezone.utc),
                UpdatedAt=datetime.now(timezone.utc),
                IsActive=True
            )
            db.add(parent_user)
            db.flush()
            
            parent_profile = ParentProfile(
                ParentID=parent_user.UserID,
                Occupation="Engineer",
                Relationship="Father",
                Address="123 Main St, Springfield"
            )
            db.add(parent_profile)

        # 5. Students
        students_data = [
            {"email": "alice@student.com", "first": "Alice", "last": "Smith", "roll": "STU001"},
            {"email": "bob@student.com", "first": "Bob", "last": "Smith", "roll": "STU002"},
        ]
        
        student_profiles = []
        for s_data in students_data:
            s_user = db.query(User).filter(User.Email == s_data["email"]).first()
            if not s_user:
                s_user = User(
                    RoleID=roles["Student"].RoleID,
                    FirstName=s_data["first"],
                    LastName=s_data["last"],
                    Email=s_data["email"],
                    PasswordHash=hash_password("Student@123"),
                    CreatedAt=datetime.now(timezone.utc),
                    UpdatedAt=datetime.now(timezone.utc),
                    IsActive=True
                )
                db.add(s_user)
                db.flush()
                
                s_profile = StudentProfile(
                    StudentID=s_user.UserID,
                    RollNumber=s_data["roll"],
                    AdmissionDate=date(2024, 8, 15),
                    AdmissionNumber=f"ADM-{s_data['roll']}",
                    Address="123 Main St, Springfield"
                )
                db.add(s_profile)
                student_profiles.append(s_profile)
                
                link = ParentStudentLink(
                    ParentID=parent_user.UserID,
                    StudentID=s_user.UserID,
                    IsPrimary=True
                )
                db.add(link)
            else:
                student_profiles.append(s_user.StudentProfile)

        # 6. Subjects
        subjects_data = [
            {"code": "MATH101", "name": "Basic Mathematics", "desc": "Fundamentals of Algebra and Geometry", "credits": 3},
            {"code": "SCI101", "name": "General Science", "desc": "Introduction to Physics, Chemistry, and Biology", "credits": 4},
        ]
        
        subjects = {}
        for sub_data in subjects_data:
            sub = db.query(Subject).filter(Subject.SubjectCode == sub_data["code"]).first()
            if not sub:
                sub = Subject(
                    SubjectCode=sub_data["code"],
                    SubjectName=sub_data["name"],
                    Description=sub_data["desc"],
                    CreditHours=sub_data["credits"]
                )
                db.add(sub)
                db.flush()
            subjects[sub_data["code"]] = sub

        # 7. Classes
        classes_data = [
            {"name": "Grade 10-A", "level": 10, "section": "A", "room": "101"},
            {"name": "Grade 10-B", "level": 10, "section": "B", "room": "102"},
        ]
        
        classes = {}
        for c_data in classes_data:
            cls = db.query(Class).filter(Class.ClassName == c_data["name"]).first()
            if not cls:
                cls = Class(
                    ClassName=c_data["name"],
                    GradeLevel=c_data["level"],
                    Section=c_data["section"],
                    AcademicYearID=ay.AcademicYearID,
                    RoomNumber=c_data["room"],
                    MaxCapacity=30,
                    CreatedAt=datetime.now(timezone.utc),
                    UpdatedAt=datetime.now(timezone.utc)
                )
                db.add(cls)
                db.flush()
            classes[c_data["name"]] = cls

        # 8. ClassSubjects
        cs1 = db.query(ClassSubject).filter(
            ClassSubject.ClassID == classes["Grade 10-A"].ClassID,
            ClassSubject.SubjectID == subjects["MATH101"].SubjectID
        ).first()
        if not cs1:
            cs1 = ClassSubject(
                ClassID=classes["Grade 10-A"].ClassID,
                SubjectID=subjects["MATH101"].SubjectID,
                TeacherID=teacher_user.UserID,
                AcademicYearID=ay.AcademicYearID,
                CreatedAt=datetime.now(timezone.utc),
                UpdatedAt=datetime.now(timezone.utc)
            )
            db.add(cs1)
            db.flush()

        cs2 = db.query(ClassSubject).filter(
            ClassSubject.ClassID == classes["Grade 10-A"].ClassID,
            ClassSubject.SubjectID == subjects["SCI101"].SubjectID
        ).first()
        if not cs2:
            cs2 = ClassSubject(
                ClassID=classes["Grade 10-A"].ClassID,
                SubjectID=subjects["SCI101"].SubjectID,
                TeacherID=teacher_user.UserID,
                AcademicYearID=ay.AcademicYearID,
                CreatedAt=datetime.now(timezone.utc),
                UpdatedAt=datetime.now(timezone.utc)
            )
            db.add(cs2)
            db.flush()

        # 9. Enrollments
        for sp in student_profiles:
            enr = db.query(Enrollment).filter(
                Enrollment.StudentID == sp.StudentID,
                Enrollment.ClassID == classes["Grade 10-A"].ClassID
            ).first()
            if not enr:
                enr = Enrollment(
                    StudentID=sp.StudentID,
                    ClassID=classes["Grade 10-A"].ClassID,
                    AcademicYearID=ay.AcademicYearID,
                    EnrollmentDate=date.today(),
                    Status="Active",
                    CreatedAt=datetime.now(timezone.utc),
                    UpdatedAt=datetime.now(timezone.utc)
                )
                db.add(enr)

        # 10. Exams
        exam1 = db.query(Exam).filter(Exam.Title == "Math Quiz 1").first()
        if not exam1:
            quiz_type = db.query(ExamType).filter(ExamType.TypeName == "Quiz").first()
            mcq_type = db.query(QuestionType).filter(QuestionType.TypeName == "MultipleChoice").first()
            
            exam1 = Exam(
                Title="Math Quiz 1",
                Description="Basic Algebra Quiz",
                ExamDate=datetime.now(timezone.utc) + timedelta(days=2),
                DurationMinutes=30,
                TotalMarks=Decimal("20.00"),
                PassingMarks=Decimal("10.00"),
                IsOnline=True,
                ClassSubjectID=cs1.ClassSubjectID,
                ExamTypeID=quiz_type.ExamTypeID,
                CreatedByID=teacher_user.UserID,
                CreatedAt=datetime.now(timezone.utc),
                UpdatedAt=datetime.now(timezone.utc)
            )
            db.add(exam1)
            db.flush()
            
            q1 = Question(
                ExamID=exam1.ExamID,
                QuestionText="What is 2 + 2?",
                QuestionTypeID=mcq_type.QuestionTypeID,
                Marks=Decimal("10.00"),
                QuestionOrder=1,
                CreatedAt=datetime.now(timezone.utc),
                UpdatedAt=datetime.now(timezone.utc)
            )
            db.add(q1)
            db.flush()
            
            opts = [
                Option(QuestionID=q1.QuestionID, OptionText="3", IsCorrect=False, OptionOrder=1, CreatedAt=datetime.now(timezone.utc)),
                Option(QuestionID=q1.QuestionID, OptionText="4", IsCorrect=True, OptionOrder=2, CreatedAt=datetime.now(timezone.utc)),
                Option(QuestionID=q1.QuestionID, OptionText="5", IsCorrect=False, OptionOrder=3, CreatedAt=datetime.now(timezone.utc)),
            ]
            db.add_all(opts)

        db.commit()
        print("Successfully seeded sample data!")
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()