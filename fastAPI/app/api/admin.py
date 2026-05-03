from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal

from app.api.deps import require_admin
from app.db.session import get_db
from app.db.entities import User, Role, StudentProfile, TeacherProfile, ParentProfile, Enrollment, Class, ParentStudentLink
from app.schemas.admin import (
    AdminDashboardStats, StudentBrief, UserAdminResponse,
    StudentCreateResponse
)
from app.schemas.common import StatusResponse
from app.core.security import hash_password

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/dashboard", response_model=AdminDashboardStats)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    total_students = db.query(StudentProfile).count()
    total_teachers = db.query(TeacherProfile).count()
    total_parents = db.query(ParentProfile).count()
    total_users = db.query(User).count()
    active_classes = db.query(Class).count()
    
    recent_users_query = db.query(User).order_by(User.CreatedAt.desc()).limit(5).all()
    recent_users = [
        {
            "user_id": u.UserID,
            "full_name": f"{u.FirstName} {u.LastName}",
            "role": u.Role.RoleName if u.Role else "N/A",
            "created_at": u.CreatedAt
        } for u in recent_users_query
    ]
    
    return AdminDashboardStats(
        total_students=total_students,
        total_teachers=total_teachers,
        total_parents=total_parents,
        total_users=total_users,
        active_classes=active_classes,
        recent_users=recent_users
    )

@router.get("/students", response_model=List[StudentBrief])
def list_students_admin(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    students = db.query(StudentProfile).all()
    result = []
    for s in students:
        user = db.query(User).filter(User.UserID == s.StudentID).first()
        if not user:
            continue
            
        # Find current class from enrollment
        enrollment = db.query(Enrollment).filter(
            Enrollment.StudentID == s.StudentID,
            Enrollment.Status == "Active"
        ).first()
        
        class_name = "Not Assigned"
        if enrollment and enrollment.ClassID:
            class_obj = db.query(Class).filter(Class.ClassID == enrollment.ClassID).first()
            if class_obj:
                class_name = class_obj.ClassName
        
        result.append(StudentBrief(
            student_id=s.StudentID,
            full_name=f"{user.FirstName} {user.LastName}",
            roll_number=s.RollNumber,
            class_name=class_name,
            is_active=user.IsActive
        ))
    return result

@router.get("/users-all", response_model=List[UserAdminResponse])
def list_all_users_admin(
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    users = db.query(User).all()
    return [
        UserAdminResponse(
            user_id=u.UserID,
            full_name=f"{u.FirstName} {u.LastName}",
            email=u.Email,
            role_name=u.Role.RoleName if u.Role else "N/A",
            is_active=u.IsActive,
            created_at=u.CreatedAt
        ) for u in users
    ]

@router.post("/users/{user_id}/toggle-status", response_model=StatusResponse)
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    user = db.query(User).filter(User.UserID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.IsActive = not user.IsActive
    db.commit()
    status_str = "activated" if user.IsActive else "deactivated"
    return StatusResponse(status="success", message=f"User {status_str} successfully")

# --- CRUD Operations for Students ---

@router.post("/students", response_model=StudentCreateResponse)
def create_student_admin(
    student_id: str = Form(..., description="Unique Student ID (e.g. 202703001)"),
    password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    roll_number: str = Form(...),
    admission_number: str = Form(...),
    admission_date: date = Form(...),
    email: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    date_of_birth: Optional[date] = Form(None),
    parent_email: Optional[str] = Form(None, description="Email of the parent to link with this student"),
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    # Check if student_id already exists
    if db.query(User).filter(User.StudentID == student_id).first():
        raise HTTPException(status_code=400, detail="Student ID already exists")

    if email and db.query(User).filter(User.Email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    student_role = db.query(Role).filter(Role.RoleName == "Student").first()
    if not student_role:
        raise HTTPException(status_code=500, detail="Student role not found in database")
    
    new_user = User(
        Email=email,
        StudentID=student_id,
        PasswordHash=hash_password(password),
        FirstName=first_name,
        LastName=last_name,
        RoleID=student_role.RoleID,
        Gender=gender,
        DateOfBirth=date_of_birth,
        IsActive=True,
        MustChangePassword=True
    )
    db.add(new_user)
    db.flush()
    
    new_profile = StudentProfile(
        StudentID=new_user.UserID,
        RollNumber=roll_number,
        AdmissionNumber=admission_number,
        AdmissionDate=admission_date,
        Address=address
    )
    db.add(new_profile)
    
    # Link parent if email provided
    if parent_email:
        parent_user = db.query(User).filter(User.Email == parent_email).first()
        if not parent_user:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Parent with email {parent_email} not found")
        
        parent_profile = db.query(ParentProfile).filter(ParentProfile.ParentID == parent_user.UserID).first()
        if not parent_profile:
            db.rollback()
            raise HTTPException(status_code=400, detail="User found but is not a parent")
            
        link = ParentStudentLink(ParentID=parent_user.UserID, StudentID=new_user.UserID)
        db.add(link)

    db.commit()
    return StudentCreateResponse(
        status="success",
        message="Student created successfully",
        student_id=student_id,
        username=student_id,
        temporary_password=password
    )

@router.put("/students/{student_id}", response_model=StatusResponse)
def update_student_admin(
    student_id: int,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    roll_number: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    parent_email: Optional[str] = Form(None, description="Email of the parent to link/add to this student"),
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    student = db.query(StudentProfile).filter(StudentProfile.StudentID == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    user = db.query(User).filter(User.UserID == student_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User record not found")
    
    if first_name is not None: user.FirstName = first_name
    if last_name is not None: user.LastName = last_name
    if is_active is not None: user.IsActive = is_active
    
    if roll_number is not None: student.RollNumber = roll_number
    if address is not None: student.Address = address

    # Handle linking a parent if email provided
    if parent_email:
        parent_user = db.query(User).filter(User.Email == parent_email).first()
        if not parent_user:
            raise HTTPException(status_code=404, detail=f"Parent with email {parent_email} not found")
        
        parent_profile = db.query(ParentProfile).filter(ParentProfile.ParentID == parent_user.UserID).first()
        if not parent_profile:
            raise HTTPException(status_code=400, detail="User found but is not a parent")
            
        # Check if link already exists
        existing_link = db.query(ParentStudentLink).filter(
            ParentStudentLink.ParentID == parent_user.UserID,
            ParentStudentLink.StudentID == student_id
        ).first()
        
        if not existing_link:
            link = ParentStudentLink(ParentID=parent_user.UserID, StudentID=student_id)
            db.add(link)
    
    db.commit()
    return StatusResponse(status="success", message="Student updated successfully")

# --- CRUD Operations for Teachers ---

@router.post("/teachers", response_model=StatusResponse)
def create_teacher_admin(
    email: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    employee_code: str = Form(...),
    qualification: Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),
    joining_date: Optional[date] = Form(None),
    salary: Optional[Decimal] = Form(None),
    gender: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    if db.query(User).filter(User.Email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    teacher_role = db.query(Role).filter(Role.RoleName == "Teacher").first()
    if not teacher_role:
        raise HTTPException(status_code=500, detail="Teacher role not found")
    
    new_user = User(
        Email=email,
        PasswordHash=hash_password(password),
        FirstName=first_name,
        LastName=last_name,
        RoleID=teacher_role.RoleID,
        Gender=gender,
        IsActive=True,
        MustChangePassword=False
    )
    db.add(new_user)
    db.flush()
    
    new_profile = TeacherProfile(
        TeacherID=new_user.UserID,
        EmployeeCode=employee_code,
        Qualification=qualification,
        Specialization=specialization,
        JoiningDate=joining_date,
        Salary=salary
    )
    db.add(new_profile)
    db.commit()
    return StatusResponse(status="success", message="Teacher created successfully")

@router.put("/teachers/{teacher_id}", response_model=StatusResponse)
def update_teacher_admin(
    teacher_id: int,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    qualification: Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),
    salary: Optional[Decimal] = Form(None),
    is_active: Optional[bool] = Form(None),
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    teacher = db.query(TeacherProfile).filter(TeacherProfile.TeacherID == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    user = db.query(User).filter(User.UserID == teacher_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User record not found")
    
    if first_name is not None: user.FirstName = first_name
    if last_name is not None: user.LastName = last_name
    if is_active is not None: user.IsActive = is_active
    
    if qualification is not None: teacher.Qualification = qualification
    if specialization is not None: teacher.Specialization = specialization
    if salary is not None: teacher.Salary = salary
    
    db.commit()
    return StatusResponse(status="success", message="Teacher updated successfully")

# --- CRUD Operations for Parents ---

@router.post("/parents", response_model=StatusResponse)
def create_parent_admin(
    email: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    occupation: Optional[str] = Form(None),
    relationship: Optional[str] = Form(None),
    alternate_phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    student_email: Optional[str] = Form(None, description="Email of the student to link with this parent"),
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    if db.query(User).filter(User.Email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    parent_role = db.query(Role).filter(Role.RoleName == "Parent").first()
    if not parent_role:
        raise HTTPException(status_code=500, detail="Parent role not found")
    
    new_user = User(
        Email=email,
        PasswordHash=hash_password(password),
        FirstName=first_name,
        LastName=last_name,
        RoleID=parent_role.RoleID,
        Gender=gender,
        IsActive=True,
        MustChangePassword=False
    )
    db.add(new_user)
    db.flush()
    
    new_profile = ParentProfile(
        ParentID=new_user.UserID,
        Occupation=occupation,
        Relationship=relationship,
        AlternatePhone=alternate_phone,
        Address=address
    )
    db.add(new_profile)
    
    # Link student if email provided
    if student_email:
        student_user = db.query(User).filter(User.Email == student_email).first()
        if not student_user:
            db.rollback()
            raise HTTPException(status_code=404, detail=f"Student with email {student_email} not found")
        
        student_profile = db.query(StudentProfile).filter(StudentProfile.StudentID == student_user.UserID).first()
        if not student_profile:
            db.rollback()
            raise HTTPException(status_code=400, detail="User found but is not a student")
            
        link = ParentStudentLink(ParentID=new_user.UserID, StudentID=student_user.UserID)
        db.add(link)

    db.commit()
    return StatusResponse(status="success", message="Parent created and linked to student successfully" if student_email else "Parent created successfully")

@router.put("/parents/{parent_id}", response_model=StatusResponse)
def update_parent_admin(
    parent_id: int,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    occupation: Optional[str] = Form(None),
    alternate_phone: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    student_email: Optional[str] = Form(None, description="Email of the student to link/add to this parent"),
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    parent = db.query(ParentProfile).filter(ParentProfile.ParentID == parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")
    
    user = db.query(User).filter(User.UserID == parent_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User record not found")
    
    if first_name is not None: user.FirstName = first_name
    if last_name is not None: user.LastName = last_name
    if is_active is not None: user.IsActive = is_active
    
    if occupation is not None: parent.Occupation = occupation
    if alternate_phone is not None: parent.AlternatePhone = alternate_phone
    
    # Handle linking a student if email provided
    if student_email:
        student_user = db.query(User).filter(User.Email == student_email).first()
        if not student_user:
            raise HTTPException(status_code=404, detail=f"Student with email {student_email} not found")
        
        student_profile = db.query(StudentProfile).filter(StudentProfile.StudentID == student_user.UserID).first()
        if not student_profile:
            raise HTTPException(status_code=400, detail="User found but is not a student")
            
        # Check if link already exists
        existing_link = db.query(ParentStudentLink).filter(
            ParentStudentLink.ParentID == parent_id,
            ParentStudentLink.StudentID == student_user.UserID
        ).first()
        
        if not existing_link:
            link = ParentStudentLink(ParentID=parent_id, StudentID=student_user.UserID)
            db.add(link)

    db.commit()
    return StatusResponse(status="success", message="Parent updated successfully")

# --- Delete Operation (Universal) ---

@router.delete("/users/{user_id}", response_model=StatusResponse)
def delete_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin)
):
    user = db.query(User).filter(User.UserID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if admin is trying to delete themselves
    if user.UserID == admin.UserID:
        raise HTTPException(status_code=400, detail="Admin cannot delete themselves")

    # Due to cascade rules or manual deletion of profiles
    # In entities.py, we might need to handle specific profile deletion if not cascading
    # For now, we assume deleting the user is enough if the DB is set up with cascades,
    # or we manually delete the profile based on the role.
    
    if user.Role:
        role_name = user.Role.RoleName
        if role_name == "Student":
            db.query(StudentProfile).filter(StudentProfile.StudentID == user_id).delete()
        elif role_name == "Teacher":
            db.query(TeacherProfile).filter(TeacherProfile.TeacherID == user_id).delete()
        elif role_name == "Parent":
            db.query(ParentProfile).filter(ParentProfile.ParentID == user_id).delete()
    
    db.delete(user)
    db.commit()
    return StatusResponse(status="success", message="User and associated profile deleted successfully")
