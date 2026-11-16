"""CRM Operations and Assignment Schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class AssignmentPreviewRequest(BaseModel):
    lead_ids: List[str] = Field(..., min_length=1)
    strategy: Optional[str] = "auto_workload"  # auto_workload, manual_single, round_robin
    target_assignee_id: Optional[str] = None

class AssignmentItemPreview(BaseModel):
    lead_id: str
    customer_name: str
    region: str
    project_name: Optional[str] = "General"
    recommended_assignee_id: str
    recommended_assignee_name: str
    reason: str
    current_workload: int

class AssignmentPreviewResponse(BaseModel):
    batch_id: str
    total_leads: int
    allocations: List[AssignmentItemPreview]

class AllocationDecision(BaseModel):
    lead_id: str
    final_assignee_id: str

class AssignmentExecutionRequest(BaseModel):
    batch_id: str
    idempotency_key: str
    approved: bool
    custom_allocations: Optional[List[AllocationDecision]] = None

class RecordExecutionDetail(BaseModel):
    lead_id: str
    assignee_id: str
    status: str
    crm_sync_status: str
    error: Optional[str] = None

class AssignmentExecutionResponse(BaseModel):
    batch_id: str
    status: str
    total_leads: int
    success_count: int
    fail_count: int
    records: List[RecordExecutionDetail]
