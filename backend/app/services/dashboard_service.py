"""Dashboard Layout Persistence, Widget Configuration, and Saved Views Service."""
import json
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.security import now_utc
from backend.app.models.identity import User
from backend.app.models.dashboards import Dashboard, DashboardWidget, SavedView, UserPreference

def get_default_layout_for_role(role: str) -> Dict[str, Any]:
    """Default enterprise widget arrangement by role."""
    base_widgets = [
        {"id": "kpi-total-leads", "type": "kpi", "metric": "total_leads", "title": "Total Leads", "position": {"x": 0, "y": 0, "w": 3, "h": 2}},
        {"id": "kpi-active-projects", "type": "kpi", "metric": "active_projects", "title": "Active Projects", "position": {"x": 3, "y": 0, "w": 3, "h": 2}},
        {"id": "kpi-conversion-rate", "type": "kpi", "metric": "conversion_rate", "title": "Conversion Rate", "position": {"x": 6, "y": 0, "w": 3, "h": 2}},
        {"id": "kpi-pipeline-value", "type": "kpi", "metric": "total_pipeline_value", "title": "Pipeline Value", "position": {"x": 9, "y": 0, "w": 3, "h": 2}},
        {"id": "chart-sales-funnel", "type": "funnel", "metric": "lead_stages", "title": "Lead Funnel", "position": {"x": 0, "y": 2, "w": 4, "h": 4}},
        {"id": "chart-performance-trend", "type": "line_chart", "metric": "monthly_revenue", "title": "Revenue & Lead Trends", "position": {"x": 4, "y": 2, "w": 5, "h": 4}},
        {"id": "feed-live-activity", "type": "activity_feed", "metric": "live_stream", "title": "Live Operations Feed", "position": {"x": 9, "y": 2, "w": 3, "h": 4}},
        {"id": "chart-project-performance", "type": "bar_chart", "metric": "project_conversion", "title": "Project Performance", "position": {"x": 0, "y": 6, "w": 6, "h": 4}},
        {"id": "chart-employee-workload", "type": "table", "metric": "employee_workload", "title": "Team Capacity & Tasks", "position": {"x": 6, "y": 6, "w": 6, "h": 4}}
    ]
    return {"columns": 12, "widgets": base_widgets}

def get_or_create_user_dashboard(db: Session, current_user: User) -> Dashboard:
    # Check if user has personal dashboard
    user_dash = db.scalar(select(Dashboard).where(Dashboard.owner_id == current_user.id).limit(1))
    if user_dash:
        return user_dash

    # Fallback to role default template or create one
    default_layout = get_default_layout_for_role(current_user.role)
    new_dash = Dashboard(
        title=f"{current_user.name}'s Command Center",
        owner_id=current_user.id,
        is_default=True,
        role_target=current_user.role,
        layout_json=json.dumps(default_layout)
    )
    db.add(new_dash)
    db.commit()
    db.refresh(new_dash)
    return new_dash

def save_dashboard_layout(
    db: Session,
    dashboard_id: str,
    layout_data: Dict[str, Any],
    current_user: User
) -> Dashboard:
    dash = db.get(Dashboard, dashboard_id)
    if not dash:
        dash = get_or_create_user_dashboard(db, current_user)

    # Permission check: owner or super_admin
    if dash.owner_id != current_user.id and current_user.role not in ("super_admin", "admin"):
        raise PermissionError("Cannot modify another user's dashboard.")

    dash.layout_json = json.dumps(layout_data)
    dash.updated_at = now_utc()
    db.commit()
    db.refresh(dash)
    return dash
