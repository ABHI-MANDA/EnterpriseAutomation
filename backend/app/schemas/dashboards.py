"""Dashboard Configuration and Saved Views Schemas."""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class WidgetPosition(BaseModel):
    x: int
    y: int
    w: int
    h: int

class DashboardWidgetSchema(BaseModel):
    id: str
    type: str  # kpi, line_chart, bar_chart, pie_chart, funnel, activity_feed, table
    metric: str
    title: str
    position: WidgetPosition
    config: Optional[Dict[str, Any]] = {}

class DashboardLayout(BaseModel):
    columns: int = 12
    widgets: List[DashboardWidgetSchema]

class DashboardOut(BaseModel):
    id: str
    title: str
    owner_id: str
    is_default: bool
    role_target: Optional[str] = None
    layout: DashboardLayout

class DashboardSaveRequest(BaseModel):
    title: str
    layout: DashboardLayout
    role_target: Optional[str] = None
    is_default: Optional[bool] = False

class SavedViewCreate(BaseModel):
    module: str
    title: str
    filters: Dict[str, Any]
    columns: List[str]
    is_shared: Optional[bool] = False

class SavedViewOut(BaseModel):
    id: str
    module: str
    title: str
    filters: Dict[str, Any]
    columns: List[str]
    is_shared: bool
