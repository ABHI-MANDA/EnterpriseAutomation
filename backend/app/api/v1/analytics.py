"""Canonical Semantic Analytics and Enterprise Dashboard Endpoints.
Covers Executive Overview, Sales Intelligence, IAM Governance, Accessibility Intelligence,
Productivity Analytics, and Distribution Reports.
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.identity import User
from backend.app.api.v1.auth import get_current_user
from backend.app.services.analytics_service import (
    get_executive_overview,
    get_sales_intelligence,
    get_employee_operations,
    get_iam_dashboard,
    get_accessibility_dashboard,
    get_productivity_dashboard,
    get_distribution_dashboard
)

router = APIRouter(tags=["Semantic Analytics & Enterprise Dashboards"])

# Overview
@router.get("/analytics/overview")
@router.get("/dashboard/overview")
def overview(
    region: Optional[str] = Query(None, description="Optional region filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_executive_overview(db, current_user, region)

# Sales Intelligence
@router.get("/analytics/sales")
@router.get("/dashboard/sales")
def sales_intelligence(
    region: Optional[str] = Query(None, description="Optional region filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_sales_intelligence(db, current_user, region)

# Employee Operations & Workload
@router.get("/analytics/workload")
def employee_workload(
    region: Optional[str] = Query(None, description="Optional region filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_employee_operations(db, current_user, region)

# IAM & Security Governance Dashboard
@router.get("/dashboard/iam")
def iam_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_iam_dashboard(db, current_user)

# Accessibility Intelligence Dashboard
@router.get("/dashboard/accessibility")
def accessibility_dashboard(
    region: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_accessibility_dashboard(db, current_user, region, from_date, to_date)

# Productivity Analytics Dashboard
@router.get("/dashboard/productivity")
def productivity_dashboard(
    region: Optional[str] = Query(None),
    period: str = Query("monthly"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_productivity_dashboard(db, current_user, region, period)

# Distribution Report & Automated Balancing
@router.get("/dashboard/distribution")
def distribution_dashboard(
    region: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_distribution_dashboard(db, current_user, region)
