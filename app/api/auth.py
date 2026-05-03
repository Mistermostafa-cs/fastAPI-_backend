from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, verify_password, hash_password
from app.db.session import get_db
from app.db.entities import Role
from app.repositories import users as user_repo
from app.schemas.auth import AuthUserResponse, TokenResponse, ChangePasswordRequest, LoginRequest
from app.schemas.common import StatusResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Login endpoint. 
    Students login using student_id.
    Others login using email.
    """
    # Clean input
    identifier = email.strip()
    
    # Fetch user by identifier (can be email or student_id)
    user = user_repo.get_user_by_identifier(db, identifier)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User not found: {identifier}",
        )

    if not bool(user.IsActive):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
        )

    # Role-based identifier validation
    # Ensure role is loaded
    if not user.Role:
        user.Role = db.query(Role).filter(Role.RoleID == user.RoleID).first()

    role_name = user.Role.RoleName if user.Role else "Unknown"
    is_student = role_name == "Student"
    
    if is_student:
        # Students must use student_id or student{id} to login
        valid_sid = user.StudentID
        valid_username = f"student{user.StudentID}".lower()
        if identifier != valid_sid and identifier.lower() != valid_username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Role mismatch: Student must use ID. Input: {identifier}",
            )
    else:
        # Others must use email to login (case-insensitive)
        if not user.Email or identifier.lower() != user.Email.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Role mismatch: {role_name} must use Email. Input: {identifier}",
            )

    if not verify_password(password, user.PasswordHash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password verification failed",
        )

    token = create_access_token(
        subject=str(user.UserID),
        email=user.Email or "",
        role=role_name,
        role_id=user.RoleID,
    )
    user_repo.set_last_login(db, user)
    
    return TokenResponse(
        access_token=token,
        user_id=user.UserID,
        full_name=f"{user.FirstName} {user.LastName}",
        email=user.Email,
        student_id=user.StudentID,
        role_name=role_name,
        must_change_password=bool(user.MustChangePassword)
    )


@router.post("/change-password", response_model=StatusResponse)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not verify_password(payload.current_password, current_user.PasswordHash):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    # Update password and clear the flag
    current_user.PasswordHash = hash_password(payload.new_password)
    current_user.MustChangePassword = False
    db.commit()
    
    return StatusResponse(status="success", message="Password updated successfully")


@router.get("/me", response_model=AuthUserResponse)
def auth_me(current_user=Depends(get_current_user)) -> AuthUserResponse:
    role_name = current_user.Role.RoleName if current_user.Role else "Unknown"
    return AuthUserResponse(
        user_id=current_user.UserID,
        full_name=f"{current_user.FirstName} {current_user.LastName}",
        email=current_user.Email,
        student_id=current_user.StudentID,
        role_id=current_user.RoleID,
        role_name=role_name,
        is_active=current_user.IsActive,
        must_change_password=current_user.MustChangePassword
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(current_user=Depends(get_current_user)) -> TokenResponse:
    if current_user.Role is None:
        raise HTTPException(status_code=500, detail="User role is missing")

    token = create_access_token(
        subject=str(current_user.UserID),
        email=current_user.Email or "",
        role=current_user.Role.RoleName,
        role_id=current_user.RoleID,
    )
    return TokenResponse(
        access_token=token,
        user_id=current_user.UserID,
        full_name=f"{current_user.FirstName} {current_user.LastName}",
        email=current_user.Email,
        student_id=current_user.StudentID,
        role_name=current_user.Role.RoleName,
        must_change_password=bool(current_user.MustChangePassword)
    )
