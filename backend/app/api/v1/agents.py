"""Natural Language AI Assistant Endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.identity import User
from backend.app.models.agents import AgentExecution
from backend.app.api.v1.auth import get_current_user
from backend.app.schemas.agents import (
    AgentChatRequest,
    AgentChatResponse,
    AgentActionExecuteRequest
)
from backend.app.agents.orchestrator import MasterOrchestrator
from backend.app.services.assignment_service import AssignmentService

router = APIRouter(prefix="/agents", tags=["AI Agent Assistant"])

@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(
    req: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = MasterOrchestrator.process_request(
        db=db,
        current_user=current_user,
        user_message=req.message,
        context_filters=req.context_filters
    )
    return AgentChatResponse(**result)

@router.post("/execute-action")
def execute_agent_action(
    req: AgentActionExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not req.approved:
        return {"status": "rejected", "message": "Action proposal was rejected by manager."}

    if req.action_type == "lead_assignment":
        payload = req.payload or {}
        allocations = payload.get("allocations", [])
        if not allocations:
            raise HTTPException(status_code=400, detail="Missing allocations in action payload.")

        batch_id = AssignmentService.create_preview_job(db, allocations, current_user)
        result = AssignmentService.execute_assignment_batch(
            db=db,
            batch_id=batch_id,
            idempotency_key=f"IDEMP-AGENT-{batch_id}",
            approved=True,
            manager=current_user
        )
        return {"status": "executed", "result": result}

    raise HTTPException(status_code=400, detail=f"Unsupported action type: {req.action_type}")

@router.get("/history")
def get_agent_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = select(AgentExecution).order_by(desc(AgentExecution.created_at)).limit(limit)
    rows = db.scalars(q).all()
    return [
        {
            "id": r.id,
            "agent_name": r.agent_name,
            "request_text": r.request_text,
            "intent": r.intent,
            "status": r.status,
            "result_summary": r.result_summary,
            "execution_time_ms": r.execution_time_ms,
            "created_at": r.created_at.isoformat() + "Z"
        } for r in rows
    ]
