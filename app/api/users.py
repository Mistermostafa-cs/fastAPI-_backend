from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.core.security import hash_password
from app.db.session import get_db
from app.repositories import roles as role_repo
from app.repositories import users as user_repo
from app.schemas.common import StatusResponse
from app.schemas.user import (
    UserCreateRequest,
    UserResponse,
    UserStatusRequest,
    UserUpdateRequest,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        user_id=current_user.UserID,
        role_id=current_user.RoleID,
        first_name=current_user.FirstName,
        last_name=current_user.LastName,
        full_name=f"{current_user.FirstName} {current_user.LastName}",
        email=current_user.Email,
        is_active=current_user.IsActive,
        created_at=current_user.CreatedAt,
        last_login_at=current_user.LastLoginAt,
    )


@router.get("", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> list[UserResponse]:
    rows = user_repo.list_users(db)
    return [
        UserResponse(
            user_id=row.UserID,
            role_id=row.RoleID,
            first_name=row.FirstName,
            last_name=row.LastName,
            full_name=f"{row.FirstName} {row.LastName}",
            email=row.Email,
            is_active=row.IsActive,
            created_at=row.CreatedAt,
            last_login_at=row.LastLoginAt,
        )
        for row in rows
    ]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> UserResponse:
    if current_user.UserID != user_id and (not current_user.Role or current_user.Role.RoleName != "Admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    row = user_repo.get_user_by_id(db, user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return UserResponse(
        user_id=row.UserID,
        role_id=row.RoleID,
        first_name=row.FirstName,
        last_name=row.LastName,
        full_name=f"{row.FirstName} {row.LastName}",
        email=row.Email,
        is_active=row.IsActive,
        created_at=row.CreatedAt,
        last_login_at=row.LastLoginAt,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    email: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(...),
    last_name: str = Form(...),
    role_id: int = Form(...),
    phone_number: str = Form(None),
    gender: str = Form(None),
    profile_photo: str = Form(None),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
) -> UserResponse:
    if user_repo.get_user_by_email(db, email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
    if role_repo.get_role_by_id(db, role_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role id")

    created = user_repo.create_user(
        db,
        RoleID=role_id,
        FirstName=first_name,
        LastName=last_name,
        Email=email,
        PasswordHash=hash_password(password),
        PhoneNumber=phone_number,
        Gender=gender,
        ProfilePhoto=profile_photo,
        CreatedBy=admin.UserID,
        MustChangePassword=False,
    )
    return UserResponse(
        user_id=created.UserID,
        role_id=created.RoleID,
        first_name=created.FirstName,
        last_name=created.LastName,
        full_name=f"{created.FirstName} {created.LastName}",
        email=created.Email,
        is_active=created.IsActive,
        created_at=created.CreatedAt,
        last_login_at=created.LastLoginAt,
    )


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    first_name: str = Form(None),
    last_name: str = Form(None),
    role_id: int = Form(None),
    phone_number: str = Form(None),
    gender: str = Form(None),
    profile_photo: str = Form(None),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
) -> UserResponse:
    row = user_repo.get_user_by_id(db, user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if role_id is not None and role_repo.get_role_by_id(db, role_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role id")

    updated = user_repo.update_user(
        db,
        row,
        **{
            k: v
            for k, v in {
                "RoleID": role_id,
                "FirstName": first_name,
                "LastName": last_name,
                "PhoneNumber": phone_number,
                "Gender": gender,
                "ProfilePhoto": profile_photo,
            }.items()
            if v is not None
        },
    )
    return UserResponse(
        user_id=updated.UserID,
        role_id=updated.RoleID,
        first_name=updated.FirstName,
        last_name=updated.LastName,
        full_name=f"{updated.FirstName} {updated.LastName}",
        email=updated.Email,
        is_active=updated.IsActive,
        created_at=updated.CreatedAt,
        last_login_at=updated.LastLoginAt,
    )


@router.patch("/{user_id}/status", response_model=StatusResponse)
def patch_user_status(
    user_id: int,
    is_active: bool = Form(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> StatusResponse:
    row = user_repo.get_user_by_id(db, user_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user_repo.update_user(db, row, IsActive=is_active)
    return StatusResponse(status="success", message="User status updated")
