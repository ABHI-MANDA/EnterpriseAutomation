"""Security, RBAC, ABAC, and Cryptographic Utilities.
Includes AES-256-GCM Field-Level Encryption & HMAC-SHA-256 Deterministic Lookup.
"""
import os
import re
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
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
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

# --- Cryptographic Utilities: AES-256-GCM & HMAC-SHA-256 ---

def _get_aes_key() -> bytes:
    """Derive 32-byte key from config for AES-256."""
    raw = settings.FIELD_ENCRYPTION_KEY.encode("utf-8")
    return hashlib.sha256(raw).digest()

def _get_hmac_key() -> bytes:
    """Derive 32-byte dedicated key for deterministic lookup."""
    raw = settings.HMAC_LOOKUP_KEY.encode("utf-8")
    return hashlib.sha256(raw).digest()

def encrypt_aes_gcm(plaintext: str, key_version: str = "v1") -> str:
    """Encrypt sensitive string using AES-256-GCM with 12-byte random IV.
    Returns: v1:<nonce_b64>:<ciphertext_and_tag_b64>
    """
    if not plaintext:
        return ""
    key = _get_aes_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    nonce_b64 = base64.b64encode(nonce).decode("ascii")
    ct_b64 = base64.b64encode(ciphertext).decode("ascii")
    return f"{key_version}:{nonce_b64}:{ct_b64}"

def decrypt_aes_gcm(encrypted_str: str) -> str:
    """Decrypt an AES-256-GCM encrypted string with authentication tag verification."""
    if not encrypted_str:
        return ""
    try:
        parts = encrypted_str.split(":")
        if len(parts) == 3:
            _, nonce_b64, ct_b64 = parts
            nonce = base64.b64decode(nonce_b64)
            ciphertext = base64.b64decode(ct_b64)
            key = _get_aes_key()
            aesgcm = AESGCM(key)
            decrypted = aesgcm.decrypt(nonce, ciphertext, None)
            return decrypted.decode("utf-8")
        return encrypted_str
    except Exception:
        # Return masked or original if failed/unencrypted
        return encrypted_str

def compute_lookup_hmac(val: str) -> str:
    """Deterministic HMAC-SHA-256 fingerprint for phone/email matching.
    Never uses unsalted SHA-256. Uses a secret HMAC key distinct from AES key.
    """
    if not val:
        return ""
    clean = str(val).strip().lower()
    key = _get_hmac_key()
    return hmac.new(key, clean.encode("utf-8"), hashlib.sha256).hexdigest()

# --- Normalization Utilities ---

def normalize_indian_mobile(phone: str) -> str:
    """Normalize Indian mobile numbers:
    - Removes spaces, dashes, +91, 0 prefix
    - Preserves clean 10-digit standard Indian format
    """
    if not phone:
        return ""
    clean = re.sub(r"[^\d]", "", str(phone))
    if clean.startswith("91") and len(clean) == 12:
        clean = clean[2:]
    elif clean.startswith("0") and len(clean) == 11:
        clean = clean[1:]
    return clean

def normalize_email(email: str) -> str:
    """Normalize email address: trim whitespace and lowercase."""
    if not email:
        return ""
    return str(email).strip().lower()

# --- Password & MFA ---

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
