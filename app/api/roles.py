from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.repositories import roles as role_repo
from app.schemas.role import RoleResponse

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=list[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    _=Depends(require_admin),
) -> list[RoleResponse]:
    roles = role_repo.list_roles(db)
    return [RoleResponse(role_id=r.RoleID, role_name=r.RoleName, description=r.Description) for r in roles]
