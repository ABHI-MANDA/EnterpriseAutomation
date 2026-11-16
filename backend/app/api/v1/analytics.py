"""Canonical Semantic Analytics Endpoints."""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.identity import User
from backend.app.api.v1.auth import get_current_user
from backend.app.services.analytics_service import (
    get_executive_overview,
    get_sales_intelligence,
    get_employee_operations
)

router = APIRouter(prefix="/analytics", tags=["Semantic Analytics"])

@router.get("/overview")
def overview(
    region: Optional[str] = Query(None, description="Optional region filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_executive_overview(db, current_user, region)

@router.get("/sales")
def sales_intelligence(
    region: Optional[str] = Query(None, description="Optional region filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_sales_intelligence(db, current_user, region)

@router.get("/workload")
def employee_workload(
    region: Optional[str] = Query(None, description="Optional region filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_employee_operations(db, current_user, region)
