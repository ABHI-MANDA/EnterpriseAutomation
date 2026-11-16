"""Dynamic Record Explorer Service.
Provides server-side pagination, multi-column filtering, sorting, and drill-downs.
All authorization and scoping are enforced server-side.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, or_, desc, asc
from sqlalchemy.orm import Session
from backend.app.core.security import ALL_SCOPE, REGION_SCOPE, mask_text, PERMS
from backend.app.models.identity import User
from backend.app.models.real_estate import Project, Property, Unit, Viewing
from backend.app.models.crm import Customer, Lead, Deal, Task, FollowUp

def query_records_paginated(
    db: Session,
    module: str,
    page: int = 1,
    limit: int = 25,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: str = "desc",
    filters: Optional[Dict[str, Any]] = None,
    current_user: User = None
) -> Dict[str, Any]:
    offset = (page - 1) * limit
    filters = filters or {}
    unmasked = current_user.role in PERMS["unmasked"]

    if module == "leads":
        q = select(Lead)
        # Regional/Role scoping
        if current_user.role in REGION_SCOPE:
            q = q.where(Lead.region == current_user.region)
        elif current_user.role not in ALL_SCOPE:
            q = q.where(Lead.assignee_id == current_user.id)

        # Apply filters
        if filters.get("region"):
            q = q.where(Lead.region == filters["region"])
        if filters.get("status"):
            q = q.where(Lead.status == filters["status"])
        if filters.get("priority"):
            q = q.where(Lead.priority == filters["priority"])
        if filters.get("source"):
            q = q.where(Lead.source == filters["source"])
        if filters.get("project_id"):
            q = q.where(Lead.project_id == filters["project_id"])
        if filters.get("assignee_id"):
            q = q.where(Lead.assignee_id == filters["assignee_id"])
        if filters.get("unassigned") is True:
            q = q.where(Lead.assignee_id.is_(None))

        # Search
        if search:
            q = q.where(or_(Lead.status.ilike(f"%{search}%"), Lead.source.ilike(f"%{search}%")))

        total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        order_col = getattr(Lead, sort_by) if (sort_by and hasattr(Lead, sort_by)) else Lead.created_at
        q = q.order_by(desc(order_col) if sort_dir == "desc" else asc(order_col)).offset(offset).limit(limit)
        items = db.scalars(q).all()

        # Join customer and assignee names
        records = []
        for l in items:
            cust = db.get(Customer, l.customer_id) if l.customer_id else None
            assignee = db.get(User, l.assignee_id) if l.assignee_id else None
            proj = db.get(Project, l.project_id) if l.project_id else None
            records.append({
                "id": l.id,
                "customer_id": l.customer_id,
                "customer_name": cust.name if cust else "Unknown",
                "customer_phone": cust.phone if (cust and unmasked) else (mask_text(cust.phone, "phone") if cust else ""),
                "customer_email": cust.email if (cust and unmasked) else (mask_text(cust.email, "email") if cust else ""),
                "project_id": l.project_id,
                "project_name": proj.name if proj else "General",
                "region": l.region,
                "branch": l.branch,
                "status": l.status,
                "priority": l.priority,
                "source": l.source,
                "budget": l.budget,
                "assignee_id": l.assignee_id,
                "assignee_name": assignee.name if assignee else "Unassigned",
                "crm_external_id": l.crm_external_id,
                "created_at": l.created_at.isoformat() + "Z"
            })
        return {"module": module, "total": total, "page": page, "limit": limit, "items": records}

    elif module == "customers":
        q = select(Customer)
        if current_user.role in REGION_SCOPE:
            q = q.where(Customer.region == current_user.region)
        elif current_user.role not in ALL_SCOPE:
            q = q.where(Customer.assignee_id == current_user.id)

        if filters.get("region"):
            q = q.where(Customer.region == filters["region"])
        if search:
            q = q.where(or_(Customer.name.ilike(f"%{search}%"), Customer.email.ilike(f"%{search}%")))

        total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        items = db.scalars(q.offset(offset).limit(limit)).all()
        records = [{
            "id": c.id,
            "name": c.name,
            "email": c.email if unmasked else mask_text(c.email, "email"),
            "phone": c.phone if unmasked else mask_text(c.phone, "phone"),
            "region": c.region,
            "source": c.source,
            "assignee_id": c.assignee_id,
            "created_at": c.created_at.isoformat() + "Z"
        } for c in items]
        return {"module": module, "total": total, "page": page, "limit": limit, "items": records}

    elif module == "projects":
        q = select(Project)
        if current_user.role in REGION_SCOPE:
            q = q.where(Project.region == current_user.region)
        if filters.get("region"):
            q = q.where(Project.region == filters["region"])
        if search:
            q = q.where(or_(Project.name.ilike(f"%{search}%"), Project.code.ilike(f"%{search}%")))

        total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        items = db.scalars(q.offset(offset).limit(limit)).all()
        records = [{
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "region": p.region,
            "project_type": p.project_type,
            "status": p.status,
            "total_units": p.total_units,
            "launch_date": p.launch_date.isoformat() + "Z"
        } for p in items]
        return {"module": module, "total": total, "page": page, "limit": limit, "items": records}

    elif module == "units":
        q = select(Unit)
        if current_user.role in REGION_SCOPE:
            q = q.where(Unit.region == current_user.region)
        if filters.get("region"):
            q = q.where(Unit.region == filters["region"])
        if filters.get("status"):
            q = q.where(Unit.status == filters["status"])
        if filters.get("bhk"):
            q = q.where(Unit.bhk == filters["bhk"])
        if search:
            q = q.where(Unit.unit_number.ilike(f"%{search}%"))

        total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        items = db.scalars(q.offset(offset).limit(limit)).all()
        records = [{
            "id": u.id,
            "unit_number": u.unit_number,
            "bhk": u.bhk,
            "area_sqft": u.area_sqft,
            "price": u.price,
            "status": u.status,
            "region": u.region,
            "project_id": u.project_id
        } for u in items]
        return {"module": module, "total": total, "page": page, "limit": limit, "items": records}

    elif module == "tasks":
        q = select(Task)
        if current_user.role in REGION_SCOPE:
            q = q.where(Task.region == current_user.region)
        elif current_user.role not in ALL_SCOPE:
            q = q.where(Task.assignee_id == current_user.id)
        if filters.get("priority"):
            q = q.where(Task.priority == filters["priority"])
        if filters.get("status") == "pending":
            q = q.where(Task.done_at.is_(None))
        elif filters.get("status") == "completed":
            q = q.where(Task.done_at.isnot(None))

        total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        items = db.scalars(q.order_by(Task.due.asc()).offset(offset).limit(limit)).all()
        records = [{
            "id": t.id,
            "title": t.title,
            "lead_id": t.lead_id,
            "assignee_id": t.assignee_id,
            "region": t.region,
            "priority": t.priority,
            "due": t.due.isoformat() + "Z",
            "done_at": t.done_at.isoformat() + "Z" if t.done_at else None
        } for t in items]
        return {"module": module, "total": total, "page": page, "limit": limit, "items": records}

    return {"module": module, "total": 0, "page": page, "limit": limit, "items": []}
