"""CRM Schemas."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., max_length=200)
    phone: str = Field(..., max_length=30)
    source: Optional[str] = "Website"
    branch: Optional[str] = ""

class CustomerOut(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    region: str
    branch: Optional[str] = ""
    source: str
    assignee_id: Optional[str] = None
    created_at: datetime

class LeadCreate(BaseModel):
    customer_id: str
    project_id: Optional[str] = None
    priority: Optional[str] = "normal"
    source: Optional[str] = "Website"
    budget: Optional[float] = 10000000.0

class LeadOut(BaseModel):
    id: str
    customer_id: str
    customer_name: Optional[str] = ""
    project_id: Optional[str] = None
    project_name: Optional[str] = ""
    region: str
    branch: Optional[str] = ""
    status: str
    priority: str
    source: str
    budget: float
    assignee_id: Optional[str] = None
    assignee_name: Optional[str] = ""
    crm_external_id: Optional[str] = None
    created_at: datetime

class TaskCreate(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = ""
    lead_id: Optional[str] = None
    assignee_id: str
    priority: Optional[str] = "normal"
    due: datetime

class TaskOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = ""
    lead_id: Optional[str] = None
    assignee_id: str
    assignee_name: Optional[str] = ""
    region: str
    priority: str
    due: datetime
    done_at: Optional[datetime] = None

class DealOut(BaseModel):
    id: str
    lead_id: str
    unit_id: Optional[str] = None
    deal_value: float
    status: str
    region: str
    expected_close_date: Optional[datetime] = None
    closed_at: Optional[datetime] = None

class FollowUpOut(BaseModel):
    id: str
    lead_id: str
    employee_id: str
    employee_name: Optional[str] = ""
    region: str
    notes: str
    outcome: str
    scheduled_at: datetime
    completed_at: Optional[datetime] = None
