from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.entities import User


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.UserID == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    if not email:
        return None
    return db.query(User).filter(User.Email.ilike(email.strip())).first()


def get_user_by_student_id(db: Session, student_id: str) -> User | None:
    if not student_id:
        return None
    return db.query(User).filter(User.StudentID == student_id.strip()).first()


def get_user_by_identifier(db: Session, identifier: str) -> User | None:
    # Try email first
    user = get_user_by_email(db, identifier)
    if user:
        return user
    
    # Try student_id
    # If identifier starts with 'student', strip it to get the ID
    sid = identifier
    if identifier.lower().startswith("student"):
        sid = identifier[7:]
    
    return get_user_by_student_id(db, sid)


def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.UserID.asc()).all()


def create_user(db: Session, **fields) -> User:
    now = datetime.now(timezone.utc)
    user = User(
        CreatedAt=now,
        UpdatedAt=now,
        IsActive=True,
        **fields,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, **fields) -> User:
    for key, value in fields.items():
        setattr(user, key, value)
    user.UpdatedAt = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    return user


def set_last_login(db: Session, user: User) -> None:
    now = datetime.now(timezone.utc)
    user.LastLoginAt = now
    user.UpdatedAt = now
    db.commit()
