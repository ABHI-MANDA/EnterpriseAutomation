"""CRM Operations Center Endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.identity import User
from backend.app.api.v1.auth import get_current_user
from backend.app.schemas.operations import (
    AssignmentPreviewRequest,
    AssignmentPreviewResponse,
    AssignmentExecutionRequest,
    AssignmentExecutionResponse
)
from backend.app.services.workload_service import evaluate_lead_allocations
from backend.app.services.assignment_service import AssignmentService

router = APIRouter(prefix="/crm-operations", tags=["CRM Operations Center"])

@router.post("/assignments/preview", response_model=AssignmentPreviewResponse)
def preview_assignments(
    req: AssignmentPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    allocations = evaluate_lead_allocations(db, req.lead_ids, current_user)
    batch_id = AssignmentService.create_preview_job(db, allocations, current_user)
    return AssignmentPreviewResponse(
        batch_id=batch_id,
        total_leads=len(allocations),
        allocations=allocations
    )

@router.post("/assignments/execute", response_model=AssignmentExecutionResponse)
def execute_assignments(
    req: AssignmentExecutionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    custom_list = [c.model_dump() for c in req.custom_allocations] if req.custom_allocations else None
    result = AssignmentService.execute_assignment_batch(
        db=db,
        batch_id=req.batch_id,
        idempotency_key=req.idempotency_key,
        approved=req.approved,
        manager=current_user,
        custom_allocations=custom_list
    )
    return AssignmentExecutionResponse(**result)
