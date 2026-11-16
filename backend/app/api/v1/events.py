"""Real-time SSE Event Stream and Operational Event History Endpoints."""
import json
import asyncio
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, Request
from starlette.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.events import broadcaster
from backend.app.core.security import ALL_SCOPE
from backend.app.models.identity import User
from backend.app.models.operations import OperationalEvent
from backend.app.api.v1.auth import get_current_user

router = APIRouter(prefix="/events", tags=["Live Activity Monitor"])

@router.get("/stream")
async def event_stream(req: Request):
    """Server-Sent Events endpoint streaming real-time platform operations."""
    async def event_generator():
        q = broadcaster.subscribe()
        try:
            # Yield initial keepalive / connection pulse
            yield f"data: {json.dumps({'event_type': 'stream.connected', 'status': 'connected'})}\n\n"
            
            # Send initial recent events
            for rec in broadcaster.get_recent()[-10:]:
                yield f"data: {json.dumps(rec)}\n\n"

            while True:
                if await req.is_disconnected():
                    break
                try:
                    event_data = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(event_data)}\n\n"
                except asyncio.TimeoutError:
                    # Ping / keepalive to keep connection open through reverse proxies
                    yield ": keepalive\n\n"
        finally:
            broadcaster.unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/history")
def event_history(
    limit: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = select(OperationalEvent)
    if event_type:
        q = q.where(OperationalEvent.event_type == event_type)
    
    q = q.order_by(desc(OperationalEvent.created_at)).limit(limit)
    rows = db.scalars(q).all()

    return [
        {
            "event_id": e.id,
            "event_type": e.event_type,
            "actor": {"id": e.actor_id, "name": e.actor_name},
            "target": {"type": e.target_type, "id": e.target_id},
            "action": {"description": e.action_desc, "status": e.status},
            "timestamp": e.created_at.isoformat() + "Z",
            "correlation_id": e.correlation_id,
            "crm_sync_status": e.crm_sync_status,
            "payload": json.loads(e.payload or "{}")
        } for e in rows
    ]
