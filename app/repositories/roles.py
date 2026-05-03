from sqlalchemy.orm import Session

from app.db.entities import Role


def list_roles(db: Session) -> list[Role]:
    return db.query(Role).order_by(Role.RoleID.asc()).all()


def get_role_by_id(db: Session, role_id: int) -> Role | None:
    return db.query(Role).filter(Role.RoleID == role_id).first()
