"""Audit Log and Cryptographic Verification Endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import PERMS
from backend.app.core.audit import verify_audit_chain, log_audit
from backend.app.models.identity import User
from backend.app.models.audit import AuditLog
from backend.app.api.v1.auth import get_current_user

router = APIRouter(prefix="/audit-logs", tags=["Governance & Tamper-Evident Audit"])

@router.get("")
def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in PERMS["audit:read"]:
        raise HTTPException(status_code=403, detail="Not authorized to inspect audit logs.")

    rows = db.scalars(select(AuditLog).order_by(desc(AuditLog.id)).limit(limit)).all()
    return [
        {
            "id": a.id,
            "ts": a.ts.isoformat() + "Z",
            "user_id": a.user_id,
            "region": a.region,
            "action": a.action,
            "resource": a.resource,
            "result": a.result,
            "ip_hash": a.ip_hash,
            "hash": a.hash
        } for a in rows
    ]

@router.get("/verify")
def verify_integrity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in PERMS["audit:read"]:
        raise HTTPException(status_code=403, detail="Not authorized.")

    intact, broken_id = verify_audit_chain(db)
    return {
        "intact": intact,
        "broken_at_entry": broken_id,
        "status": "Audit hash chain cryptographically verified" if intact else "TAMPERING DETECTED"
    }
