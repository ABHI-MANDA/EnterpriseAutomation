"""Universal Database Record Explorer Endpoints."""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.identity import User
from backend.app.api.v1.auth import get_current_user
from backend.app.services.record_service import query_records_paginated

router = APIRouter(prefix="/records", tags=["Record Explorer"])

@router.get("/{module}")
def get_records(
    module: str,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_dir: str = Query("desc", pattern="^(asc|desc)$"),
    region: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    assignee_id: Optional[str] = Query(None),
    unassigned: Optional[bool] = Query(None),
    city_id: Optional[str] = Query(None),
    locality_id: Optional[str] = Query(None),
    zone_id: Optional[str] = Query(None),
    property_type_id: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    allocated_to: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    filters = {}
    if region:
        filters["region"] = region
    if status:
        filters["status"] = status
    if priority:
        filters["priority"] = priority
    if source:
        filters["source"] = source
    if project_id:
        filters["project_id"] = project_id
    if assignee_id:
        filters["assignee_id"] = assignee_id
    if unassigned is not None:
        filters["unassigned"] = unassigned
    if city_id:
        filters["city_id"] = city_id
    if locality_id:
        filters["locality_id"] = locality_id
    if zone_id:
        filters["zone_id"] = zone_id
    if property_type_id:
        filters["property_type_id"] = property_type_id
    if min_price is not None:
        filters["min_price"] = min_price
    if max_price is not None:
        filters["max_price"] = max_price
    if allocated_to:
        filters["allocated_to"] = allocated_to

    return query_records_paginated(
        db=db,
        module=module,
        page=page,
        limit=limit,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        filters=filters,
        current_user=current_user
    )
