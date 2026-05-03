from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Role(Base):
    __tablename__ = "Roles"

    RoleID: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    RoleName: Mapped[str] = mapped_column(String(60), unique=True)
    Description: Mapped[str | None] = mapped_column(String(255))

    Users: Mapped[list[User]] = relationship(back_populates="Role")


class User(Base):
    __tablename__ = "Users"

    UserID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    RoleID: Mapped[int] = mapped_column(ForeignKey("Roles.RoleID"))
    FirstName: Mapped[str] = mapped_column(String(100))
    LastName: Mapped[str] = mapped_column(String(100))
    Email: Mapped[str | None] = mapped_column(String(255), unique=True)
    StudentID: Mapped[str | None] = mapped_column(String(20), unique=True, index=True)
    PasswordHash: Mapped[str] = mapped_column(String(512))
    MustChangePassword: Mapped[bool] = mapped_column(Boolean, default=True)
    PhoneNumber: Mapped[str | None] = mapped_column(String(20))
    Gender: Mapped[str | None] = mapped_column(String(10))
    DateOfBirth: Mapped[date | None] = mapped_column(Date)
    ProfilePhoto: Mapped[str | None] = mapped_column(String(500))
    IsActive: Mapped[bool] = mapped_column(Boolean, default=True)
    LastLoginAt: Mapped[datetime | None] = mapped_column(DateTime)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    CreatedBy: Mapped[int | None]

    Role: Mapped[Role] = relationship(back_populates="Users")
    AdminProfile: Mapped[AdminProfile | None] = relationship(back_populates="User")
    TeacherProfile: Mapped[TeacherProfile | None] = relationship(back_populates="User")
    StudentProfile: Mapped[StudentProfile | None] = relationship(back_populates="User")
    ParentProfile: Mapped[ParentProfile | None] = relationship(back_populates="User")


class AdminProfile(Base):
    __tablename__ = "AdminProfiles"

    AdminID: Mapped[int] = mapped_column(ForeignKey("Users.UserID"), primary_key=True)
    EmployeeCode: Mapped[str] = mapped_column(String(20))
    Department: Mapped[str | None] = mapped_column(String(100))
    AccessLevel: Mapped[int]
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    User: Mapped[User] = relationship(back_populates="AdminProfile")


class TeacherProfile(Base):
    __tablename__ = "TeacherProfiles"

    TeacherID: Mapped[int] = mapped_column(ForeignKey("Users.UserID"), primary_key=True)
    EmployeeCode: Mapped[str] = mapped_column(String(20))
    Qualification: Mapped[str | None] = mapped_column(String(255))
    Specialization: Mapped[str | None] = mapped_column(String(255))
    JoiningDate: Mapped[date | None] = mapped_column(Date)
    Salary: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    User: Mapped[User] = relationship(back_populates="TeacherProfile")
    Assignments: Mapped[list[Assignment]] = relationship(back_populates="CreatedBy")
    GradedSubmissions: Mapped[list[AssignmentSubmission]] = relationship(back_populates="GradedBy")
    AttendanceMarked: Mapped[list[Attendance]] = relationship(back_populates="MarkedBy")
    ExamsCreated: Mapped[list[Exam]] = relationship(back_populates="CreatedBy")
    GradesEntered: Mapped[list[Grade]] = relationship(back_populates="InputBy")
    GradedAnswers: Mapped[list[StudentAnswer]] = relationship(back_populates="GradedBy")


class StudentProfile(Base):
    __tablename__ = "StudentProfiles"

    StudentID: Mapped[int] = mapped_column(ForeignKey("Users.UserID"), primary_key=True)
    RollNumber: Mapped[str] = mapped_column(String(20))
    AdmissionDate: Mapped[date] = mapped_column(Date)
    AdmissionNumber: Mapped[str] = mapped_column(String(30))
    Address: Mapped[str | None] = mapped_column(String(500))
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    User: Mapped[User] = relationship(back_populates="StudentProfile")
    Enrollments: Mapped[list[Enrollment]] = relationship(back_populates="Student")
    Submissions: Mapped[list[AssignmentSubmission]] = relationship(back_populates="Student")
    Attendance: Mapped[list[Attendance]] = relationship(back_populates="Student")
    ExamSessions: Mapped[list[ExamSession]] = relationship(back_populates="Student")
    Grades: Mapped[list[Grade]] = relationship(back_populates="Student")
    Parents: Mapped[list[ParentStudentLink]] = relationship(back_populates="Student")


class ParentProfile(Base):
    __tablename__ = "ParentProfiles"

    ParentID: Mapped[int] = mapped_column(ForeignKey("Users.UserID"), primary_key=True)
    Occupation: Mapped[str | None] = mapped_column(String(150))
    Relationship: Mapped[str | None] = mapped_column(String(50))
    AlternatePhone: Mapped[str | None] = mapped_column(String(20))
    Address: Mapped[str | None] = mapped_column(Text)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    User: Mapped[User] = relationship(back_populates="ParentProfile")
    Children: Mapped[list[ParentStudentLink]] = relationship(back_populates="Parent")


class ParentStudentLink(Base):
    __tablename__ = "ParentStudentLinks"

    LinkID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ParentID: Mapped[int] = mapped_column(ForeignKey("ParentProfiles.ParentID"))
    StudentID: Mapped[int] = mapped_column(ForeignKey("StudentProfiles.StudentID"))
    IsPrimary: Mapped[bool] = mapped_column(Boolean, default=True)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    Parent: Mapped[ParentProfile] = relationship(back_populates="Children")
    Student: Mapped[StudentProfile] = relationship(back_populates="Parents")


class AcademicYear(Base):
    __tablename__ = "AcademicYears"

    AcademicYearID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    YearLabel: Mapped[str] = mapped_column(String(20))
    StartDate: Mapped[date] = mapped_column(Date)
    EndDate: Mapped[date] = mapped_column(Date)
    IsCurrent: Mapped[bool] = mapped_column(Boolean, default=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Class(Base):
    __tablename__ = "Classes"

    ClassID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ClassName: Mapped[str] = mapped_column(String(100))
    GradeLevel: Mapped[int]
    Section: Mapped[str | None] = mapped_column(String(10))
    AcademicYearID: Mapped[int] = mapped_column(ForeignKey("AcademicYears.AcademicYearID"))
    ClassTeacherID: Mapped[int | None] = mapped_column(ForeignKey("TeacherProfiles.TeacherID"))
    MaxCapacity: Mapped[int | None]
    RoomNumber: Mapped[str | None] = mapped_column(String(20))
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Subject(Base):
    __tablename__ = "Subjects"

    SubjectID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    SubjectCode: Mapped[str] = mapped_column(String(20))
    SubjectName: Mapped[str] = mapped_column(String(150))
    Description: Mapped[str | None] = mapped_column(String(500))
    CreditHours: Mapped[int | None]
    IsElective: Mapped[bool] = mapped_column(Boolean, default=False)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClassSubject(Base):
    __tablename__ = "ClassSubjects"

    ClassSubjectID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ClassID: Mapped[int] = mapped_column(ForeignKey("Classes.ClassID"))
    SubjectID: Mapped[int] = mapped_column(ForeignKey("Subjects.SubjectID"))
    TeacherID: Mapped[int] = mapped_column(ForeignKey("TeacherProfiles.TeacherID"))
    AcademicYearID: Mapped[int] = mapped_column(ForeignKey("AcademicYears.AcademicYearID"))
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    Assignments: Mapped[list[Assignment]] = relationship(back_populates="ClassSubject")
    Attendance: Mapped[list[Attendance]] = relationship(back_populates="ClassSubject")
    Exams: Mapped[list[Exam]] = relationship(back_populates="ClassSubject")
    Grades: Mapped[list[Grade]] = relationship(back_populates="ClassSubject")
    TeacherProfile: Mapped[TeacherProfile] = relationship(foreign_keys=[TeacherID])
    Subject: Mapped[Subject] = relationship(foreign_keys=[SubjectID])


class Enrollment(Base):
    __tablename__ = "Enrollments"

    EnrollmentID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    StudentID: Mapped[int] = mapped_column(ForeignKey("StudentProfiles.StudentID"))
    ClassID: Mapped[int] = mapped_column(ForeignKey("Classes.ClassID"))
    AcademicYearID: Mapped[int] = mapped_column(ForeignKey("AcademicYears.AcademicYearID"))
    EnrollmentDate: Mapped[date] = mapped_column(Date)
    Status: Mapped[str] = mapped_column(String(20), default="Active")
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    Student: Mapped[StudentProfile] = relationship(back_populates="Enrollments")


class Assignment(Base):
    __tablename__ = "Assignments"

    AssignmentID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ClassSubjectID: Mapped[int] = mapped_column(ForeignKey("ClassSubjects.ClassSubjectID"))
    Title: Mapped[str] = mapped_column(String(255))
    Description: Mapped[str | None] = mapped_column(Text)
    DueDate: Mapped[datetime] = mapped_column(DateTime)
    MaxMarks: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=100.00)
    CreatedByID: Mapped[int] = mapped_column(ForeignKey("TeacherProfiles.TeacherID"))
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ClassSubject: Mapped[ClassSubject] = relationship(back_populates="Assignments")
    CreatedBy: Mapped[TeacherProfile] = relationship(back_populates="Assignments")
    Submissions: Mapped[list[AssignmentSubmission]] = relationship(back_populates="Assignment")


class AssignmentSubmission(Base):
    __tablename__ = "AssignmentSubmissions"

    SubmissionID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    AssignmentID: Mapped[int] = mapped_column(ForeignKey("Assignments.AssignmentID"))
    StudentID: Mapped[int] = mapped_column(ForeignKey("StudentProfiles.StudentID"))
    SubmittedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    FilePath: Mapped[str | None] = mapped_column(String(500))
    Comments: Mapped[str | None] = mapped_column(Text)
    MarksObtained: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    GradedByID: Mapped[int | None] = mapped_column(ForeignKey("TeacherProfiles.TeacherID"))
    GradedAt: Mapped[datetime | None] = mapped_column(DateTime)
    Status: Mapped[str] = mapped_column(String(20), default="Submitted")
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    Assignment: Mapped[Assignment] = relationship(back_populates="Submissions")
    Student: Mapped[StudentProfile] = relationship(back_populates="Submissions")
    GradedBy: Mapped[TeacherProfile | None] = relationship(back_populates="GradedSubmissions")


class Attendance(Base):
    __tablename__ = "Attendance"

    AttendanceID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    StudentID: Mapped[int] = mapped_column(ForeignKey("StudentProfiles.StudentID"))
    ClassSubjectID: Mapped[int] = mapped_column(ForeignKey("ClassSubjects.ClassSubjectID"))
    AttendanceDate: Mapped[date] = mapped_column(Date)
    Status: Mapped[str] = mapped_column(String(10), default="Present")
    Remarks: Mapped[str | None] = mapped_column(String(255))
    MarkedByID: Mapped[int] = mapped_column(ForeignKey("TeacherProfiles.TeacherID"))
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    Student: Mapped[StudentProfile] = relationship(back_populates="Attendance")
    ClassSubject: Mapped[ClassSubject] = relationship(back_populates="Attendance")
    MarkedBy: Mapped[TeacherProfile] = relationship(back_populates="AttendanceMarked")


class ExamType(Base):
    __tablename__ = "ExamTypes"

    ExamTypeID: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    TypeName: Mapped[str] = mapped_column(String(50))

    Exams: Mapped[list[Exam]] = relationship(back_populates="ExamType")


class Exam(Base):
    __tablename__ = "Exams"

    ExamID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ClassSubjectID: Mapped[int] = mapped_column(ForeignKey("ClassSubjects.ClassSubjectID"))
    ExamTypeID: Mapped[int] = mapped_column(ForeignKey("ExamTypes.ExamTypeID"))
    Title: Mapped[str] = mapped_column(String(255))
    Description: Mapped[str | None] = mapped_column(Text)
    ExamDate: Mapped[datetime] = mapped_column(DateTime)
    DurationMinutes: Mapped[int] = mapped_column(default=60)
    TotalMarks: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=100.00)
    PassingMarks: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=40.00)
    IsOnline: Mapped[bool] = mapped_column(Boolean, default=True)
    CreatedByID: Mapped[int] = mapped_column(ForeignKey("TeacherProfiles.TeacherID"))
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ClassSubject: Mapped[ClassSubject] = relationship(back_populates="Exams")
    ExamType: Mapped[ExamType] = relationship(back_populates="Exams")
    CreatedBy: Mapped[TeacherProfile] = relationship(back_populates="ExamsCreated")
    Questions: Mapped[list[Question]] = relationship(back_populates="Exam")
    ExamSessions: Mapped[list[ExamSession]] = relationship(back_populates="Exam")
    Grades: Mapped[list[Grade]] = relationship(back_populates="Exam")


class QuestionType(Base):
    __tablename__ = "QuestionTypes"

    QuestionTypeID: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    TypeName: Mapped[str] = mapped_column(String(50))

    Questions: Mapped[list[Question]] = relationship(back_populates="QuestionType")


class Question(Base):
    __tablename__ = "Questions"

    QuestionID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ExamID: Mapped[int] = mapped_column(ForeignKey("Exams.ExamID"))
    QuestionTypeID: Mapped[int] = mapped_column(ForeignKey("QuestionTypes.QuestionTypeID"))
    QuestionText: Mapped[str] = mapped_column(Text)
    QuestionOrder: Mapped[int] = mapped_column(default=1)
    Marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=1.00)
    DifficultyLevel: Mapped[int | None]
    Explanation: Mapped[str | None] = mapped_column(Text)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    Exam: Mapped[Exam] = relationship(back_populates="Questions")
    QuestionType: Mapped[QuestionType] = relationship(back_populates="Questions")
    Options: Mapped[list[Option]] = relationship(back_populates="Question")
    StudentAnswers: Mapped[list[StudentAnswer]] = relationship(back_populates="Question")


class Option(Base):
    __tablename__ = "Options"

    OptionID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    QuestionID: Mapped[int] = mapped_column(ForeignKey("Questions.QuestionID"))
    OptionText: Mapped[str] = mapped_column(Text)
    IsCorrect: Mapped[bool] = mapped_column(Boolean, default=False)
    OptionOrder: Mapped[int] = mapped_column(default=1)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    Question: Mapped[Question] = relationship(back_populates="Options")
    StudentAnswers: Mapped[list[StudentAnswer]] = relationship(back_populates="SelectedOption")


class ExamSession(Base):
    __tablename__ = "ExamSessions"

    SessionID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ExamID: Mapped[int] = mapped_column(ForeignKey("Exams.ExamID"))
    StudentID: Mapped[int] = mapped_column(ForeignKey("StudentProfiles.StudentID"))
    StartedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    SubmittedAt: Mapped[datetime | None] = mapped_column(DateTime)
    TotalScore: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    IsPassed: Mapped[bool | None] = mapped_column(Boolean)
    Status: Mapped[str] = mapped_column(String(20), default="InProgress")
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    Exam: Mapped[Exam] = relationship(back_populates="ExamSessions")
    Student: Mapped[StudentProfile] = relationship(back_populates="ExamSessions")
    StudentAnswers: Mapped[list[StudentAnswer]] = relationship(back_populates="Session")


class StudentAnswer(Base):
    __tablename__ = "StudentAnswers"

    AnswerID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    SessionID: Mapped[int] = mapped_column(ForeignKey("ExamSessions.SessionID"))
    QuestionID: Mapped[int] = mapped_column(ForeignKey("Questions.QuestionID"))
    SelectedOptionID: Mapped[int | None] = mapped_column(ForeignKey("Options.OptionID"))
    AnswerText: Mapped[str | None] = mapped_column(Text)
    MarksAwarded: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    IsCorrect: Mapped[bool | None] = mapped_column(Boolean)
    TeacherFeedback: Mapped[str | None] = mapped_column(Text)
    GradedByID: Mapped[int | None] = mapped_column(ForeignKey("TeacherProfiles.TeacherID"))
    GradedAt: Mapped[datetime | None] = mapped_column(DateTime)
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    Session: Mapped[ExamSession] = relationship(back_populates="StudentAnswers")
    Question: Mapped[Question] = relationship(back_populates="StudentAnswers")
    SelectedOption: Mapped[Option | None] = relationship(back_populates="StudentAnswers")
    GradedBy: Mapped[TeacherProfile | None] = relationship(back_populates="GradedAnswers")


class GradeScale(Base):
    __tablename__ = "GradeScales"

    GradeScaleID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    GradeLetter: Mapped[str] = mapped_column(String(5))
    MinPercentage: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    MaxPercentage: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    GradePoint: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    Remarks: Mapped[str | None] = mapped_column(String(50))

    Grades: Mapped[list[Grade]] = relationship(back_populates="GradeScale")


class Grade(Base):
    __tablename__ = "Grades"

    GradeID: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    StudentID: Mapped[int] = mapped_column(ForeignKey("StudentProfiles.StudentID"))
    ClassSubjectID: Mapped[int] = mapped_column(ForeignKey("ClassSubjects.ClassSubjectID"))
    AcademicYearID: Mapped[int] = mapped_column(ForeignKey("AcademicYears.AcademicYearID"))
    ExamID: Mapped[int | None] = mapped_column(ForeignKey("Exams.ExamID"))
    MarksObtained: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    TotalMarks: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    Percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    IsPassed: Mapped[bool | None] = mapped_column(Boolean)
    GradeScaleID: Mapped[int | None] = mapped_column(ForeignKey("GradeScales.GradeScaleID"))
    Remarks: Mapped[str | None] = mapped_column(String(255))
    InputByID: Mapped[int] = mapped_column(ForeignKey("TeacherProfiles.TeacherID"))
    CreatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    UpdatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    Student: Mapped[StudentProfile] = relationship(back_populates="Grades")
    ClassSubject: Mapped[ClassSubject] = relationship(back_populates="Grades")
    AcademicYear: Mapped[AcademicYear] = relationship()
    Exam: Mapped[Exam | None] = relationship(back_populates="Grades")
    GradeScale: Mapped[GradeScale | None] = relationship(back_populates="Grades")
    InputBy: Mapped[TeacherProfile] = relationship(back_populates="GradesEntered")

