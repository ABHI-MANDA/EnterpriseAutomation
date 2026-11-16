"""Canonical Semantic Analytics Schemas."""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ExecutiveOverviewResponse(BaseModel):
    total_customers: int
    total_leads: int
    active_leads: int
    active_projects: int
    available_units: int
    reserved_units: int
    sold_units: int
    total_deals: int
    total_pipeline_value: float
    closed_revenue: float
    conversion_rate: float
    pending_followups: int
    overdue_tasks: int
    crm_sync_health: str
    security_alerts_7d: int

class LeadStageBreakdown(BaseModel):
    stage: str
    count: int
    percentage: float

class MonthlyTrend(BaseModel):
    month: str
    leads: int
    conversions: int
    revenue: float

class ProjectPerformance(BaseModel):
    project_id: str
    project_name: str
    region: str
    leads_count: int
    deals_count: int
    conversion_rate: float
    revenue: float

class RegionPerformance(BaseModel):
    region: str
    leads_count: int
    conversions: int
    conversion_rate: float
    unassigned_leads: int

class EmployeeWorkload(BaseModel):
    employee_id: str
    name: str
    region: str
    assigned_leads: int
    open_tasks: int
    completed_tasks: int
    overdue_tasks: int
    conversion_rate: float
    overloaded: bool
