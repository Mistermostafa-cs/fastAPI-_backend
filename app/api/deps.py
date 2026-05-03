from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token, parse_subject
from app.core.config import settings
from app.db.entities import User
from app.db.session import get_db

security = HTTPBearer()


def get_current_user(
    db: Session = Depends(get_db),
    auth: HTTPAuthorizationCredentials = Depends(security),
) -> Any:
    token = auth.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = parse_subject(payload)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.UserID == user_id).first()
    if user is None or not user.IsActive:
        raise credentials_exception
    return user


def require_admin(current_user: Any = Depends(get_current_user)) -> Any:
    if not current_user.Role or current_user.Role.RoleName != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_student(current_user: Any = Depends(get_current_user)) -> Any:
    if not current_user.Role or current_user.Role.RoleName != "Student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )
    return current_user


def require_teacher(current_user: Any = Depends(get_current_user)) -> Any:
    if not current_user.Role or current_user.Role.RoleName != "Teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher access required",
        )
    return current_user


def require_parent(current_user: Any = Depends(get_current_user)) -> Any:
    if not current_user.Role or current_user.Role.RoleName != "Parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Parent access required",
        )
    return current_user
