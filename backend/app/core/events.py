"""Standardized Event System and Real-time SSE Broadcaster."""
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, AsyncGenerator, List
from sqlalchemy.orm import Session
from backend.app.core.security import now_utc

class EventBroadcaster:
    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []
        self._recent_events: List[Dict[str, Any]] = []
        self._max_recent = 50

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._subscribers:
            self._subscribers.remove(q)

    def broadcast(self, event_data: Dict[str, Any]):
        self._recent_events.append(event_data)
        if len(self._recent_events) > self._max_recent:
            self._recent_events.pop(0)

        dead_queues = []
        for q in self._subscribers:
            try:
                q.put_nowait(event_data)
            except asyncio.QueueFull:
                dead_queues.append(q)
            except Exception:
                dead_queues.append(q)
        for q in dead_queues:
            self.unsubscribe(q)

    def get_recent(self) -> List[Dict[str, Any]]:
        return list(self._recent_events)

broadcaster = EventBroadcaster()

def publish_event(
    db: Session,
    event_type: str,
    actor: Dict[str, Any],
    target: Dict[str, Any],
    action_desc: str,
    status: str = "completed",
    crm_sync_status: str = "success",
    correlation_id: str | None = None,
    payload: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    from backend.app.models.operations import OperationalEvent
    from backend.app.models.integration import Outbox

    event_id = str(uuid.uuid4())
    cid = correlation_id or str(uuid.uuid4())
    ts = now_utc().isoformat() + "Z"

    event_dict = {
        "event_id": event_id,
        "event_type": event_type,
        "actor": actor,
        "target": target,
        "action": {
            "description": action_desc,
            "status": status
        },
        "source": "command_center",
        "timestamp": ts,
        "correlation_id": cid,
        "crm_sync_status": crm_sync_status,
        "payload": payload or {}
    }

    # Persist in operational_events table
    op_event = OperationalEvent(
        id=event_id,
        event_type=event_type,
        actor_id=actor.get("id", "system"),
        actor_name=actor.get("name", "System"),
        target_type=target.get("type", "record"),
        target_id=target.get("id", ""),
        action_desc=action_desc,
        status=status,
        crm_sync_status=crm_sync_status,
        correlation_id=cid,
        payload=json.dumps(payload or {})
    )
    db.add(op_event)

    # If relevant to CRM, write to Outbox
    if crm_sync_status in ("pending", "sync_required"):
        outbox_entry = Outbox(
            id=str(uuid.uuid4()),
            event=event_type,
            payload=json.dumps(event_dict),
            status="pending"
        )
        db.add(outbox_entry)

    db.commit()

    # Broadcast to SSE
    try:
        broadcaster.broadcast(event_dict)
    except Exception:
        pass

    return event_dict
