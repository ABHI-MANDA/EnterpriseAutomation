"""Dynamic Record Explorer Service.
Provides server-side pagination, multi-column filtering, sorting, and drill-downs.
All authorization and scoping are enforced server-side.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, or_, and_, desc, asc
from sqlalchemy.orm import Session
from backend.app.core.security import ALL_SCOPE, REGION_SCOPE, mask_text, PERMS
from backend.app.models.identity import User
from backend.app.models.organization import City, Zone, Locality
from backend.app.models.real_estate import Project, Property, Unit, Viewing, PropertyType
from backend.app.models.crm import Customer, Lead, Deal, Task, FollowUp, LeadAllocation
from backend.app.models.ingestion import UnmatchedEntity, ImportBatch, DuplicateCandidate

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
    unmasked = current_user.role in PERMS["unmasked"] if current_user else False

    if module == "leads":
        q = select(Lead)
        # Regional/Role scoping
        if current_user and current_user.role in REGION_SCOPE:
            q = q.where(Lead.region == current_user.region)
        elif current_user and current_user.role not in ALL_SCOPE:
            q = q.where(or_(Lead.assignee_id == current_user.id, Lead.allocated_to == current_user.id))

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
        if filters.get("allocated_to"):
            q = q.where(or_(Lead.allocated_to == filters["allocated_to"], Lead.assignee_id == filters["allocated_to"]))
        if filters.get("unassigned") is True:
            q = q.where(and_(Lead.assignee_id.is_(None), Lead.allocated_to.is_(None)))
        if filters.get("city_id"):
            q = q.where(Lead.city_id == filters["city_id"])
        if filters.get("locality_id"):
            q = q.where(Lead.locality_id == filters["locality_id"])
        if filters.get("zone_id"):
            q = q.where(Lead.zone_id == filters["zone_id"])
        if filters.get("property_type_id"):
            q = q.where(Lead.property_type_id == filters["property_type_id"])
        if filters.get("min_price") is not None:
            q = q.where(or_(Lead.max_price >= filters["min_price"], Lead.budget >= filters["min_price"]))
        if filters.get("max_price") is not None:
            q = q.where(or_(Lead.min_price <= filters["max_price"], Lead.budget <= filters["max_price"]))

        # Search
        if search:
            q = q.where(or_(
                Lead.name.ilike(f"%{search}%"),
                Lead.status.ilike(f"%{search}%"),
                Lead.source.ilike(f"%{search}%")
            ))

        total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        order_col = getattr(Lead, sort_by) if (sort_by and hasattr(Lead, sort_by)) else Lead.created_at
        q = q.order_by(desc(order_col) if sort_dir == "desc" else asc(order_col)).offset(offset).limit(limit)
        items = db.scalars(q).all()

        records = []
        for l in items:
            cust = db.get(Customer, l.customer_id) if l.customer_id else None
            assignee = db.get(User, l.assignee_id) if l.assignee_id else None
            allocated_user = db.get(User, l.allocated_to) if l.allocated_to else None
            proj = db.get(Project, l.project_id) if l.project_id else None
            ptype = db.get(PropertyType, l.property_type_id) if l.property_type_id else None
            city = db.get(City, l.city_id) if l.city_id else None
            loc = db.get(Locality, l.locality_id) if l.locality_id else None
            zone = db.get(Zone, l.zone_id) if l.zone_id else None

            lead_name = l.name or (cust.name if cust else "Unknown")
            records.append({
                "id": l.id,
                "name": lead_name,
                "customer_id": l.customer_id,
                "customer_name": cust.name if cust else lead_name,
                "customer_phone": cust.phone if (cust and unmasked) else (mask_text(cust.phone, "phone") if cust else ""),
                "customer_email": cust.email if (cust and unmasked) else (mask_text(cust.email, "email") if cust else ""),
                "project_id": l.project_id,
                "project_name": proj.name if proj else "General",
                "property_type_id": l.property_type_id,
                "property_type_name": ptype.name if ptype else "Apartment",
                "city_id": l.city_id,
                "city_name": city.name if city else "",
                "locality_id": l.locality_id,
                "locality_name": loc.name if loc else "",
                "zone_id": l.zone_id,
                "zone_name": zone.name if zone else "",
                "region": l.region,
                "branch": l.branch,
                "status": l.status,
                "priority": l.priority,
                "source": l.source,
                "budget": l.budget,
                "min_price": l.min_price,
                "max_price": l.max_price,
                "assignee_id": l.assignee_id,
                "assignee_name": assignee.name if assignee else "Unassigned",
                "allocated_to": l.allocated_to or l.assignee_id,
                "allocated_to_name": allocated_user.name if allocated_user else (assignee.name if assignee else "Unassigned"),
                "allocated_date": l.allocated_date.isoformat() + "Z" if l.allocated_date else None,
                "crm_external_id": l.crm_external_id,
                "has_encrypted_pii": bool(l.mobile_encrypted or l.email_encrypted),
                "created_at": l.created_at.isoformat() + "Z"
            })
        return {"module": module, "total": total, "page": page, "limit": limit, "items": records}

    elif module == "customers":
        q = select(Customer)
        if current_user and current_user.role in REGION_SCOPE:
            q = q.where(Customer.region == current_user.region)
        elif current_user and current_user.role not in ALL_SCOPE:
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
        if current_user and current_user.role in REGION_SCOPE:
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
            "city_id": p.city_id,
            "locality_id": p.locality_id,
            "zone_id": p.zone_id,
            "launch_date": p.launch_date.isoformat() + "Z"
        } for p in items]
        return {"module": module, "total": total, "page": page, "limit": limit, "items": records}

    elif module == "units":
        q = select(Unit)
        if current_user and current_user.role in REGION_SCOPE:
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
        if current_user and current_user.role in REGION_SCOPE:
            q = q.where(Task.region == current_user.region)
        elif current_user and current_user.role not in ALL_SCOPE:
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

    elif module == "cities":
        q = select(City)
        if search:
            q = q.where(City.name.ilike(f"%{search}%"))
        total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        items = db.scalars(q.offset(offset).limit(limit)).all()
        records = [{"id": c.id, "name": c.name, "state": c.state, "country": c.country} for c in items]
        return {"module": module, "total": total, "page": page, "limit": limit, "items": records}

    elif module == "zones":
        q = select(Zone)
        if search:
            q = q.where(Zone.name.ilike(f"%{search}%"))
        total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        items = db.scalars(q.offset(offset).limit(limit)).all()
        records = [{"id": z.id, "name": z.name} for z in items]
        return {"module": module, "total": total, "page": page, "limit": limit, "items": records}

    elif module == "localities":
        q = select(Locality)
        if filters.get("city_id"):
            q = q.where(Locality.city_id == filters["city_id"])
        if filters.get("zone_id"):
            q = q.where(Locality.zone_id == filters["zone_id"])
        if search:
            q = q.where(Locality.name.ilike(f"%{search}%"))
        total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        items = db.scalars(q.offset(offset).limit(limit)).all()
        records = [{"id": l.id, "name": l.name, "city_id": l.city_id, "zone_id": l.zone_id} for l in items]
        return {"module": module, "total": total, "page": page, "limit": limit, "items": records}

    elif module == "property_types":
        q = select(PropertyType)
        if search:
            q = q.where(or_(PropertyType.name.ilike(f"%{search}%"), PropertyType.code.ilike(f"%{search}%")))
        total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        items = db.scalars(q.offset(offset).limit(limit)).all()
        records = [{"id": pt.id, "name": pt.name, "code": pt.code} for pt in items]
        return {"module": module, "total": total, "page": page, "limit": limit, "items": records}

    elif module == "lead_allocations":
        q = select(LeadAllocation)
        if filters.get("lead_id"):
            q = q.where(LeadAllocation.lead_id == filters["lead_id"])
        if filters.get("employee_id"):
            q = q.where(LeadAllocation.employee_id == filters["employee_id"])
        total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        items = db.scalars(q.order_by(desc(LeadAllocation.allocated_date)).offset(offset).limit(limit)).all()
        records = [{
            "id": la.id,
            "lead_id": la.lead_id,
            "employee_id": la.employee_id,
            "previous_employee_id": la.previous_employee_id,
            "allocated_date": la.allocated_date.isoformat() + "Z",
            "allocated_by": la.allocated_by,
            "allocation_status": la.allocation_status,
            "notes": la.notes
        } for la in items]
        return {"module": module, "total": total, "page": page, "limit": limit, "items": records}

    elif module == "unmatched_entities":
        q = select(UnmatchedEntity)
        if filters.get("batch_id"):
            q = q.where(UnmatchedEntity.batch_id == filters["batch_id"])
        if filters.get("entity_type"):
            q = q.where(UnmatchedEntity.entity_type == filters["entity_type"])
        total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
        items = db.scalars(q.order_by(desc(UnmatchedEntity.created_at)).offset(offset).limit(limit)).all()
        records = [{
            "id": ue.id,
            "batch_id": ue.batch_id,
            "raw_value": ue.raw_value,
            "entity_type": ue.entity_type,
            "suggested_match": ue.suggested_match,
            "context_info": getattr(ue, 'context_info', None),
            "resolution_status": getattr(ue, 'resolution_status', ue.status),
            "resolved_to_id": getattr(ue, 'resolved_to_id', None),
            "status": ue.status,
            "created_at": ue.created_at.isoformat() + "Z"
        } for ue in items]
        return {"module": module, "total": total, "page": page, "limit": limit, "items": records}

    return {"module": module, "total": 0, "page": page, "limit": limit, "items": []}
