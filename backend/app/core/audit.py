"""Tamper-evident, hash-chained audit logging and verification."""
import hashlib
import threading
from datetime import datetime
from typing import Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.security import now_utc, hash_ip

_audit_lock = threading.Lock()

def compute_audit_hash(prev_hash: str, record: Dict[str, Any]) -> str:
    parts = [
        prev_hash,
        str(record.get("ts")),
        str(record.get("user_id")),
        str(record.get("action")),
        str(record.get("resource", "")),
        str(record.get("result", ""))
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def log_audit(
    db: Session,
    user_id: str,
    action: str,
    resource: str = "",
    result: str = "SUCCESS",
    region: str = "",
    ip_hashed: str = ""
):
    from backend.app.models.audit import AuditLog
    with _audit_lock:
        last = db.scalar(select(AuditLog).order_by(AuditLog.id.desc()).limit(1))
        prev_hash = last.hash if last else "0" * 64
        rec = {
            "ts": now_utc(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "result": result
        }
        digest = compute_audit_hash(prev_hash, rec)
        audit_entry = AuditLog(
            ts=rec["ts"],
            user_id=user_id,
            region=region,
            action=action,
            resource=resource,
            result=result,
            ip_hash=ip_hashed,
            prev_hash=prev_hash,
            hash=digest
        )
        db.add(audit_entry)
        db.commit()

def verify_audit_chain(db: Session) -> Tuple[bool, int | None]:
    from backend.app.models.audit import AuditLog
    prev = "0" * 64
    logs = db.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    for entry in logs:
        rec = {
            "ts": entry.ts,
            "user_id": entry.user_id,
            "action": entry.action,
            "resource": entry.resource,
            "result": entry.result
        }
        expected = compute_audit_hash(prev, rec)
        if entry.prev_hash != prev or entry.hash != expected:
            return False, entry.id
        prev = entry.hash
    return True, None
