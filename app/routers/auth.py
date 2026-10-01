"""Auth routes: register / login / refresh / logout / verify / password reset.

Conventions: versioned under /api/v1/auth, JSON errors {detail, code},
OAuth2-password compatible /token endpoint for Swagger Authorize button.
"""
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token, create_refresh_token, decode_token,
    generate_raw_token, hash_password, hash_token, verify_password,
)
from app.db.session import get_db
from app.models.observability import AuditLog
from app.models.user import (
    EmailVerificationToken, PasswordResetToken, RevokedToken, Role, User,
)
from app.schemas import (
    ForgotPasswordIn, LoginIn, RefreshIn, RegisterIn, ResetPasswordIn,
    TokenOut, UserOut, VerifyEmailIn,
)
from app.services.email_service import send_email

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def _audit(db: Session, *, user_id: int | None, action: str, ip: str = "") -> None:
    db.add(AuditLog(user_id=user_id, action=action, entity_type="user",
                    entity_id=str(user_id) if user_id else None, ip_address=ip or None))


def _tokens_for(user: User) -> TokenOut:
    access, _, _ = create_access_token(user_id=user.id, role=user.role)
    refresh, _, _ = create_refresh_token(user_id=user.id, role=user.role)
    return TokenOut(access_token=access, refresh_token=refresh)


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    role = data.role.upper()
    if role not in (User.CUSTOMER, User.SELLER):
        raise HTTPException(403, "Only CUSTOMER or SELLER can self-register; SUPPORT/ADMIN via admin.")
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    role_row = db.query(Role).filter(Role.name == role).first()
    user = User(email=data.email.lower(), password_hash=hash_password(data.password),
                full_name=data.full_name, role=role,
                role_id=role_row.id if role_row else None)
    db.add(user)
    db.flush()
    raw = generate_raw_token()
    db.add(EmailVerificationToken(
        user_id=user.id, token_hash=hash_token(raw),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)))
    _audit(db, user_id=user.id, action="user.register")
    db.commit()
    db.refresh(user)
    send_email(user.email, "Verify your email",
               f"Hi {user.full_name or user.email}, verify with this token (24h):\n{raw}")
    return user


def _check_lock(user: User) -> None:
    if user.status == "locked":
        raise HTTPException(423, "Account locked after repeated failed logins. Reset password or contact support.")


def _do_login(db: Session, email: str, password: str) -> TokenOut:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not verify_password(password, user.password_hash):
        if user:
            user.failed_logins += 1
            if user.failed_logins >= settings.FAILED_LOGIN_LIMIT:
                user.status = "locked"
                _audit(db, user_id=user.id, action="user.locked")
            db.commit()
        raise HTTPException(401, "Invalid credentials")
    _check_lock(user)
    user.failed_logins = 0
    _audit(db, user_id=user.id, action="user.login")
    db.commit()
    return _tokens_for(user)


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    return _do_login(db, data.email, data.password)


@router.post("/token", response_model=TokenOut, include_in_schema=False)
def oauth_token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """OAuth2 password flow (scopes = roles) for Swagger UI Authorize button."""
    return _do_login(db, form.username, form.password)


@router.post("/refresh", response_model=TokenOut)
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    try:
        payload = decode_token(data.refresh_token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Refresh token required")
    if db.query(RevokedToken).filter(RevokedToken.jti == payload.get("jti")).first():
        raise HTTPException(401, "Refresh token revoked")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or user.status != "active":
        raise HTTPException(401, "User inactive")
    # Rotation: revoke old refresh token.
    db.add(RevokedToken(jti=payload["jti"], user_id=user.id,
                        expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc)))
    _audit(db, user_id=user.id, action="user.token_refresh")
    db.commit()
    return _tokens_for(user)


@router.post("/logout", status_code=204)
def logout(data: RefreshIn | None = None, user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    # Revoke current access token is handled by client dropping it; here we revoke
    # the paired refresh token if supplied (standard rotation logout).
    if data and data.refresh_token:
        try:
            payload = decode_token(data.refresh_token)
            if payload.get("type") == "refresh":
                db.add(RevokedToken(jti=payload["jti"], user_id=user.id,
                                    expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc)))
        except jwt.InvalidTokenError:
            pass
    _audit(db, user_id=user.id, action="user.logout")
    db.commit()
    return None


@router.post("/verify-email")
def verify_email(data: VerifyEmailIn, db: Session = Depends(get_db)):
    token = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token_hash == hash_token(data.token),
        EmailVerificationToken.used == False).first()  # noqa: E712
    if not token or token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "Invalid or expired verification token")
    user = db.query(User).filter(User.id == token.user_id).first()
    user.email_verified = True
    token.used = True
    _audit(db, user_id=user.id, action="user.email_verified")
    db.commit()
    return {"ok": True}


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordIn, db: Session = Depends(get_db)):
    # Always 200 to avoid email enumeration.
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if user:
        raw = generate_raw_token()
        db.add(PasswordResetToken(
            user_id=user.id, token_hash=hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)))
        db.commit()
        send_email(user.email, "Password reset",
                   f"Reset within 1 hour with this token:\n{raw}")
    return {"ok": True, "message": "If the email exists, a reset link was sent."}


@router.post("/reset-password")
def reset_password(data: ResetPasswordIn, db: Session = Depends(get_db)):
    token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == hash_token(data.token),
        PasswordResetToken.used == False).first()  # noqa: E712
    if not token or token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(400, "Invalid or expired reset token")
    user = db.query(User).filter(User.id == token.user_id).first()
    user.password_hash = hash_password(data.new_password)
    user.failed_logins = 0
    user.status = "active"  # unlock on successful reset
    token.used = True
    _audit(db, user_id=user.id, action="user.password_reset")
    db.commit()
    return {"ok": True}
