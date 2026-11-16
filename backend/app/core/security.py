"""Security, RBAC, ABAC, and Cryptographic Utilities."""
import os
import hmac
import hashlib
import base64
import struct
import time
import secrets
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import threading
import jwt
from fastapi import HTTPException, Request, Depends
from sqlalchemy.orm import Session
from backend.app.core.config import settings

# RBAC Hierarchy & Scopes
ALL_SCOPE = {"super_admin", "admin", "management", "auditor"}
REGION_SCOPE = {"regional_manager", "dept_manager"}
PERMS = {
    "audit:read": {"super_admin", "admin", "auditor", "management"},
    "export": {"super_admin", "management", "regional_manager"},
    "customer:write": {"super_admin", "admin", "regional_manager", "employee"},
    "lead:assign": {"super_admin", "admin", "management", "regional_manager"},
    "lead:write": {"super_admin", "admin", "regional_manager", "employee"},
    "dashboard:manage": {"super_admin", "admin", "management"},
    "unmasked": {"super_admin", "admin"}
}

def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def hash_pw(pw: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', pw.encode(), salt.encode(), 600_000).hex()
    return f"{salt}${hashed}"

def check_pw(pw: str, stored: str) -> bool:
    try:
        salt = stored.split("$")[0]
        return hmac.compare_digest(hash_pw(pw, salt), stored)
    except Exception:
        return False

def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode()

def totp_code(secret: str, t: float | None = None) -> str:
    c = int((t or time.time()) // 30)
    h = hmac.new(base64.b32decode(secret), struct.pack(">Q", c), "sha1").digest()
    o = h[-1] & 15
    return f"{(struct.unpack('>I', h[o:o+4])[0] & 0x7fffffff) % 10**6:06d}"

def verify_totp(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    return any(hmac.compare_digest(totp_code(secret, time.time() + d * 30), code.strip()) for d in (-1, 0, 1))

# Rate limiting
_hits = defaultdict(list)
_rl_lock = threading.Lock()

def check_rate_limit(key: str, limit: int = 15, window: int = 60):
    t = time.time()
    with _rl_lock:
        _hits[key] = [x for x in _hits[key] if t - x < window]
        if len(_hits[key]) >= limit:
            raise HTTPException(status_code=429, detail="Too many attempts. Please try again shortly.")
        _hits[key].append(t)

def hash_ip(req: Request) -> str:
    client_ip = req.client.host if req.client else "unknown"
    return hashlib.sha256((settings.SECRET_KEY + client_ip).encode()).hexdigest()[:16]

def mask_text(val: str, kind: str) -> str:
    if not val:
        return ""
    if kind == "email" and "@" in val:
        user_part, domain = val.split("@", 1)
        return user_part[:1] + "***@" + domain
    if kind == "phone":
        return "***" + val[-4:] if len(val) >= 4 else "***"
    return "***"

def create_access_token(user_id: str, role: str, region: str) -> str:
    expire = now_utc() + timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "region": region,
        "exp": expire
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authorization token.")
