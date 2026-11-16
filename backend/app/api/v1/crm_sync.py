"""CRM Integration & Bidirectional Synchronization Endpoints."""
import json
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.identity import User
from backend.app.models.integration import Outbox, ConflictLog
from backend.app.api.v1.auth import get_current_user
from backend.app.services.crm_adapter import CRMAdapter

router = APIRouter(prefix="/integrations/crm", tags=["CRM Integration"])

@router.post("/webhook")
async def inbound_crm_webhook(
    req: Request,
    x_signature: str = Header(None),
    db: Session = Depends(get_db)
):
    body = await req.body()
    if not CRMAdapter.verify_webhook_signature(body, x_signature or ""):
        raise HTTPException(status_code=401, detail="Invalid HMAC webhook signature.")

    try:
        data = json.loads(body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.")

    return CRMAdapter.process_inbound_webhook(db, data)

@router.post("/outbox/process")
def process_outbox(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ("super_admin", "admin", "management"):
        raise HTTPException(status_code=403, detail="Not authorized.")
    processed = CRMAdapter.process_outbox_queue(db)
    return {"status": "success", "processed_events": processed}

@router.get("/health")
def crm_health(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pending = db.scalar(select(func.count(Outbox.id)).where(Outbox.status == "pending")) or 0
    failed = db.scalar(select(func.count(Outbox.id)).where(Outbox.status == "failed")) or 0
    conflicts = db.scalar(select(func.count(ConflictLog.id)).where(ConflictLog.resolution == "unresolved")) or 0

    return {
        "status": "Healthy" if failed == 0 else "Degraded",
        "pending_outbox_events": pending,
        "failed_outbox_events": failed,
        "unresolved_conflicts": conflicts
    }
