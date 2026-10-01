"""User profile, addresses, admin user management (RBAC demo surface)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import RequireAdmin, get_current_user
from app.db.session import get_db
from app.models.observability import AuditLog
from app.models.user import Address, Role, User
from app.schemas import AddressIn, AddressOut, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user.id).first()
    if "full_name" in payload:
        u.full_name = str(payload["full_name"])[:255]
    db.add(AuditLog(user_id=u.id, action="user.profile_update", entity_type="user", entity_id=str(u.id)))
    db.commit()
    db.refresh(u)
    return u


@router.get("/me/addresses", response_model=list[AddressOut])
def list_addresses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Address).filter(Address.user_id == user.id).all()


@router.post("/me/addresses", response_model=AddressOut, status_code=201)
def add_address(data: AddressIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    addr = Address(user_id=user.id, **data.model_dump())
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


# --- Admin only ---
@router.get("", response_model=list[UserOut], dependencies=[Depends(RequireAdmin)])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).limit(100).all()


@router.patch("/{user_id}/role", response_model=UserOut)
def set_role(user_id: int, payload: dict, admin: User = Depends(RequireAdmin), db: Session = Depends(get_db)):
    role = str(payload.get("role", "")).upper()
    if role not in User.ALL_ROLES:
        raise HTTPException(400, f"Invalid role. Choose from {list(User.ALL_ROLES)}")
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "User not found")
    role_row = db.query(Role).filter(Role.name == role).first()
    u.role = role
    u.role_id = role_row.id if role_row else None
    db.add(AuditLog(user_id=admin.id, action="admin.role_change", entity_type="user", entity_id=str(u.id)))
    db.commit()
    db.refresh(u)
    return u


@router.post("/{user_id}/unlock", response_model=UserOut)
def unlock(user_id: int, admin: User = Depends(RequireAdmin), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404, "User not found")
    u.status = "active"
    u.failed_logins = 0
    db.commit()
    db.refresh(u)
    return u
