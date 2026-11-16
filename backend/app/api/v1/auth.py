"""Authentication Endpoints with MFA and Rate Limiting."""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.core.database import get_db, set_rls_context
from backend.app.core.security import (
    check_pw, hash_pw, verify_totp, generate_totp_secret,
    check_rate_limit, hash_ip, create_access_token, decode_access_token, now_utc
)
from backend.app.core.audit import log_audit
from backend.app.models.identity import User
from backend.app.schemas.auth import LoginRequest, LoginResponse, MFAEnrollResponse, UserOut

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_current_user(req: Request, db: Session = Depends(get_db)) -> User:
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication token required.")
    
    token = auth_header[7:]
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    
    user = db.get(User, user_id)
    if not user or not user.active:
        raise HTTPException(status_code=401, detail="User account is inactive or not found.")
    
    set_rls_context(db, user.id, user.role, user.region)
    return user

@router.post("/login", response_model=LoginResponse)
def login(login_req: LoginRequest, req: Request, db: Session = Depends(get_db)):
    client_ip_h = hash_ip(req)
    check_rate_limit(f"login:{client_ip_h}", limit=settings.MAX_LOGIN_FAILURES * 2, window=60)

    user = db.scalar(select(User).where(User.email == login_req.email.lower().strip()))
    bad_creds = HTTPException(status_code=401, detail="Email, password or authenticator code is incorrect.")

    if not user or not user.active:
        check_pw(login_req.password, hash_pw("dummy_salt_hash"))
        log_audit(db, "unknown", "LOGIN", result="FAILURE", ip_hashed=client_ip_h)
        raise bad_creds

    # Lockout check
    if user.locked_until and user.locked_until > now_utc():
        log_audit(db, user.id, "LOGIN_LOCKED", result="FAILURE", region=user.region, ip_hashed=client_ip_h)
        raise HTTPException(status_code=423, detail="Account is temporarily locked due to multiple failed attempts.")

    # Password & MFA verification
    pw_valid = check_pw(login_req.password, user.pw_hash)
    mfa_valid = True
    if user.mfa_secret:
        mfa_valid = verify_totp(user.mfa_secret, login_req.otp or "")

    if not (pw_valid and mfa_valid):
        user.fails += 1
        if user.fails >= settings.MAX_LOGIN_FAILURES:
            user.locked_until = now_utc() + timedelta(minutes=settings.LOCKOUT_MINUTES)
            user.fails = 0
        db.commit()
        log_audit(db, user.id, "LOGIN", result="FAILURE", region=user.region, ip_hashed=client_ip_h)
        raise bad_creds

    # Successful login
    user.fails = 0
    user.locked_until = None
    user.last_login_at = now_utc()
    db.commit()

    log_audit(db, user.id, "LOGIN", result="SUCCESS", region=user.region, ip_hashed=client_ip_h)
    token = create_access_token(user.id, user.role, user.region)

    return LoginResponse(
        token=token,
        user=UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            department=user.department,
            region=user.region,
            branch=user.branch or "",
            expertise=user.expertise or ""
        )
    )

@router.post("/mfa/enroll", response_model=MFAEnrollResponse)
def enroll_mfa(req: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = generate_totp_secret()
    current_user.mfa_secret = secret
    db.commit()
    log_audit(db, current_user.id, "MFA_ENROLLED", region=current_user.region)
    return MFAEnrollResponse(secret=secret)

@router.get("/me", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        department=current_user.department,
        region=current_user.region,
        branch=current_user.branch or "",
        expertise=current_user.expertise or ""
    )
