"""AI Agent Interface and Execution Schemas."""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class AgentChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context_filters: Optional[Dict[str, Any]] = None

class AgentToolCallDetail(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    output: Any

class AgentEvidence(BaseModel):
    title: str
    data_points: List[str]
    supporting_record_ids: Optional[List[str]] = []

class AgentProposedAction(BaseModel):
    action_type: str  # lead_assignment, task_creation, report_export
    summary: str
    details: Dict[str, Any]
    requires_approval: bool = True

class AgentChatResponse(BaseModel):
    execution_id: str
    agent_name: str
    intent: str
    message: str
    interpreted_filters: Optional[Dict[str, Any]] = None
    evidence: Optional[List[AgentEvidence]] = None
    proposed_action: Optional[AgentProposedAction] = None
    execution_status: str

class AgentActionExecuteRequest(BaseModel):
    execution_id: str
    action_type: str
    approved: bool
    payload: Optional[Dict[str, Any]] = None
