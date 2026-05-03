from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from decimal import Decimal

from app.api.deps import get_current_user
from app.db.session import get_db
from app.repositories import profiles as profile_repo
from app.repositories import users as user_repo
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/profiles", tags=["Profiles"])


@router.get("/{user_id}", response_model=ProfileResponse)
def get_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ProfileResponse:
    if current_user.UserID != user_id and (not current_user.Role or current_user.Role.RoleName != "Admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    target = user_repo.get_user_by_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role_name = target.Role.RoleName if target.Role else "Unknown"
    profile = profile_repo.get_profile_for_user(db, target)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    data = {key: value for key, value in profile.__dict__.items() if not key.startswith("_")}
    return ProfileResponse(user_id=user_id, role_name=role_name, profile=data)


@router.put("/{user_id}", response_model=ProfileResponse)
def update_profile(
    user_id: int,
    department: Optional[str] = Form(None),
    access_level: Optional[int] = Form(None),
    qualification: Optional[str] = Form(None),
    specialization: Optional[str] = Form(None),
    joining_date: Optional[date] = Form(None),
    salary: Optional[Decimal] = Form(None),
    roll_number: Optional[str] = Form(None),
    admission_date: Optional[date] = Form(None),
    admission_number: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    occupation: Optional[str] = Form(None),
    relationship: Optional[str] = Form(None),
    alternate_phone: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ProfileResponse:
    if current_user.UserID != user_id and (not current_user.Role or current_user.Role.RoleName != "Admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    target = user_repo.get_user_by_id(db, user_id)
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role_name = target.Role.RoleName if target.Role else "Unknown"
    profile = profile_repo.get_profile_for_user(db, target)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    raw_updates = {
        "department": department,
        "access_level": access_level,
        "qualification": qualification,
        "specialization": specialization,
        "joining_date": joining_date,
        "salary": salary,
        "roll_number": roll_number,
        "admission_date": admission_date,
        "admission_number": admission_number,
        "address": address,
        "occupation": occupation,
        "relationship": relationship,
        "alternate_phone": alternate_phone,
    }
    
    mapped_updates = {
        "department": "Department",
        "access_level": "AccessLevel",
        "qualification": "Qualification",
        "specialization": "Specialization",
        "joining_date": "JoiningDate",
        "salary": "Salary",
        "roll_number": "RollNumber",
        "admission_date": "AdmissionDate",
        "admission_number": "AdmissionNumber",
        "address": "Address",
        "occupation": "Occupation",
        "relationship": "Relationship",
        "alternate_phone": "AlternatePhone",
    }
    updates = {mapped_updates[k]: v for k, v in raw_updates.items() if v is not None and k in mapped_updates}

    if updates:
        profile = profile_repo.update_profile(db, profile, updates)
    data = {key: value for key, value in profile.__dict__.items() if not key.startswith("_")}
    return ProfileResponse(user_id=user_id, role_name=role_name, profile=data)
