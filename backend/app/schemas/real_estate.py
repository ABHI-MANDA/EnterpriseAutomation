"""Real Estate Domain Schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProjectOut(BaseModel):
    id: str
    name: str
    code: str
    region: str
    branch: Optional[str] = ""
    project_type: str
    status: str
    total_units: int
    launch_date: datetime

class PropertyOut(BaseModel):
    id: str
    project_id: str
    name: str
    total_floors: int
    region: str

class UnitOut(BaseModel):
    id: str
    project_id: str
    property_id: str
    unit_number: str
    bhk: str
    area_sqft: float
    price: float
    status: str
    region: str

class ViewingOut(BaseModel):
    id: str
    unit_id: str
    lead_id: str
    employee_id: str
    scheduled_at: datetime
    status: str
    feedback: Optional[str] = ""
