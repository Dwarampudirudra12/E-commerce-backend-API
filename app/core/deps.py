"""Authentication + RBAC dependencies (doc 3.1 permission matrix)."""
import uuid
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.user import RevokedToken, User

bearer = HTTPBearer(auto_error=False)

# Capability -> allowed roles (mirrors doc permission matrix, Page 3).
CAPABILITIES: dict[str, set[str]] = {
    "browse_catalog": {"CUSTOMER", "SELLER", "SUPPORT", "ADMIN"},
    "manage_cart_order": {"CUSTOMER"},
    "view_own_orders": {"CUSTOMER"},
    "create_product": {"SELLER", "ADMIN"},
    "update_inventory": {"SELLER", "ADMIN"},
    "view_all_orders": {"SUPPORT", "ADMIN"},
    "review_fraud": {"SUPPORT", "ADMIN"},
    "issue_refund": {"SUPPORT", "ADMIN"},
    "manage_users": {"ADMIN"},
    "view_analytics": {"SELLER", "SUPPORT", "ADMIN"},
    "view_audit": {"ADMIN"},
}


def _request_id() -> str:
    return str(uuid.uuid4())[:8]


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    settings = get_settings()
    try:
        payload = jwt.decode(creds.credentials, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Access token required")
    # Revocation check (logout).
    if db.query(RevokedToken).filter(RevokedToken.jti == payload.get("jti")).first():
        raise HTTPException(status_code=401, detail="Token revoked")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or user.status != "active":
        raise HTTPException(status_code=401, detail="User inactive or missing")
    return user


def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Requires one of {list(roles)}")
        return user
    return checker


def require_capability(capability: str):
    allowed = CAPABILITIES[capability]
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail=f"Capability '{capability}' not allowed for {user.role}")
        return user
    return checker

# Shortcuts used by routers.
RequireAdmin = require_roles("ADMIN")
RequireSupport = require_roles("SUPPORT", "ADMIN")
RequireSeller = require_roles("SELLER", "ADMIN")
