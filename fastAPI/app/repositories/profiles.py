from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.db.entities import AdminProfile, ParentProfile, TeacherProfile, StudentProfile, User


def get_profile_for_user(db: Session, user: User) -> Any | None:
    if user.Role and user.Role.RoleName == "Admin":
        return db.query(AdminProfile).filter(AdminProfile.AdminID == user.UserID).first()
    if user.Role and user.Role.RoleName == "Teacher":
        return db.query(TeacherProfile).filter(TeacherProfile.TeacherID == user.UserID).first()
    if user.Role and user.Role.RoleName == "Student":
        return db.query(StudentProfile).filter(StudentProfile.StudentID == user.UserID).first()
    if user.Role and user.Role.RoleName == "Parent":
        return db.query(ParentProfile).filter(ParentProfile.ParentID == user.UserID).first()
    return None


def update_profile(db: Session, profile: Any, payload: dict[str, Any]) -> Any:
    for key, value in payload.items():
        setattr(profile, key, value)
    if hasattr(profile, "UpdatedAt"):
        profile.UpdatedAt = datetime.now(timezone.utc)
    db.commit()
    db.refresh(profile)
    return profile
