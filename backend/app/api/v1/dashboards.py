"""Dashboard Engine and Customization Endpoints."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.identity import User
from backend.app.models.dashboards import Dashboard, SavedView
from backend.app.api.v1.auth import get_current_user
from backend.app.schemas.dashboards import (
    DashboardOut,
    DashboardSaveRequest,
    SavedViewCreate,
    SavedViewOut
)
from backend.app.services.dashboard_service import (
    get_or_create_user_dashboard,
    save_dashboard_layout
)

router = APIRouter(prefix="/dashboards", tags=["Customizable Dashboards"])

@router.get("/my")
def get_my_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dash = get_or_create_user_dashboard(db, current_user)
    layout = json.loads(dash.layout_json or "{}")
    return {
        "id": dash.id,
        "title": dash.title,
        "owner_id": dash.owner_id,
        "is_default": dash.is_default,
        "role_target": dash.role_target,
        "layout": layout
    }

@router.post("/save")
def save_dashboard(
    req: DashboardSaveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    dash = get_or_create_user_dashboard(db, current_user)
    updated = save_dashboard_layout(db, dash.id, req.layout.model_dump(), current_user)
    return {
        "status": "saved",
        "id": updated.id,
        "title": updated.title,
        "updated_at": updated.updated_at.isoformat() + "Z"
    }

@router.post("/saved-views")
def create_saved_view(
    req: SavedViewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    view = SavedView(
        user_id=current_user.id,
        module=req.module,
        title=req.title,
        filters_json=json.dumps(req.filters),
        columns_json=json.dumps(req.columns),
        is_shared=req.is_shared or False
    )
    db.add(view)
    db.commit()
    db.refresh(view)
    return {
        "id": view.id,
        "module": view.module,
        "title": view.title,
        "filters": req.filters,
        "columns": req.columns,
        "is_shared": view.is_shared
    }

@router.get("/saved-views/{module}")
def get_saved_views(
    module: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    views = db.scalars(
        select(SavedView).where(
            SavedView.module == module,
            (SavedView.user_id == current_user.id) | (SavedView.is_shared == True)
        )
    ).all()

    return [
        {
            "id": v.id,
            "module": v.module,
            "title": v.title,
            "filters": json.loads(v.filters_json or "{}"),
            "columns": json.loads(v.columns_json or "[]"),
            "is_shared": v.is_shared
        } for v in views
    ]
