"""CRM Core Entities: Customers, Leads, Assignments, Activities, and Consent (DPDP Act)."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import (
    now_utc, ALL_SCOPE, REGION_SCOPE, PERMS, mask_text,
    encrypt_aes_gcm, decrypt_aes_gcm, compute_lookup_hmac,
    normalize_indian_mobile, normalize_email
)
from backend.app.core.audit import log_audit
from backend.app.models.identity import User
from backend.app.models.crm import Customer, Lead, Task, FollowUp, Activity, Communication, ConsentRecord
from backend.app.models.operations import OperationalEvent
from backend.app.api.v1.auth import get_current_user
from backend.app.services.assignment_service import AssignmentService
from backend.app.services.crm_adapter import CRMAdapter

router = APIRouter(tags=["CRM Core Entities"])

# --- Schemas ---

class CustomerCreate(BaseModel):
    name: str
    phone: str
    email: str
    region: str
    branch: Optional[str] = ""
    source: Optional[str] = "Website"
    consent_purpose: Optional[str] = "property_consultation"

class LeadCreate(BaseModel):
    customer_id: str
    project_id: Optional[str] = None
    region: str
    branch: Optional[str] = ""
    priority: Optional[str] = "normal"
    source: Optional[str] = "Website"
    budget: Optional[float] = 10000000.0
    assignee_id: Optional[str] = None

class AssignmentRequest(BaseModel):
    lead_id: str
    employee_id: str
    notes: Optional[str] = "Manual management assignment from command center."

class ActivityCreate(BaseModel):
    activity_type: str
    entity_type: str
    entity_id: str
    description: str
    region: Optional[str] = ""

class ConsentCreate(BaseModel):
    customer_id: str
    purpose: str
    provenance: str = "web_portal"
    notice_version: str = "DPDP-2023-V1"

# --- Endpoints ---

@router.get("/customers")
def list_customers(
    search: Optional[str] = Query(None),
    region: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = select(Customer)
    if current_user.role in REGION_SCOPE:
        q = q.where(Customer.region == current_user.region)
    elif current_user.role not in ALL_SCOPE:
        q = q.where(Customer.assignee_id == current_user.id)
    
    if region and (current_user.role in ALL_SCOPE or region == current_user.region):
        q = q.where(Customer.region == region)

    if search:
        s_clean = search.strip()
        # Check if searching by mobile/email via HMAC deterministic lookup
        norm_phone = normalize_indian_mobile(s_clean)
        norm_email = normalize_email(s_clean)
        phone_hmac = compute_lookup_hmac(norm_phone)
        email_hmac = compute_lookup_hmac(norm_email)
        q = q.where(
            (Customer.name.ilike(f"%{s_clean}%")) |
            (Customer.phone_lookup_hmac == phone_hmac) |
            (Customer.email_lookup_hmac == email_hmac)
        )

    customers = db.scalars(q.order_by(desc(Customer.created_at)).limit(limit)).all()
    unmasked = current_user.role in PERMS["unmasked"]

    res = []
    for c in customers:
        raw_phone = c.phone
        raw_email = c.email
        # If encrypted, decrypt if authorized
        if c.phone_encrypted and unmasked:
            raw_phone = decrypt_aes_gcm(c.phone_encrypted)
        if c.email_encrypted and unmasked:
            raw_email = decrypt_aes_gcm(c.email_encrypted)

        display_phone = raw_phone if unmasked else mask_text(raw_phone, "phone")
        display_email = raw_email if unmasked else mask_text(raw_email, "email")

        res.append({
            "id": c.id,
            "name": c.name,
            "phone": display_phone,
            "email": display_email,
            "region": c.region,
            "branch": c.branch,
            "source": c.source,
            "created_at": c.created_at.isoformat() + "Z"
        })
    return res

@router.post("/customers")
def create_customer(
    req: CustomerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in PERMS["customer:write"]:
        raise HTTPException(status_code=403, detail="Not authorized to create customer records.")

    norm_phone = normalize_indian_mobile(req.phone)
    norm_email = normalize_email(req.email)
    phone_hmac = compute_lookup_hmac(norm_phone)
    email_hmac = compute_lookup_hmac(norm_email)

    # Check for existing duplicate by HMAC deterministic fingerprint
    existing = db.scalar(
        select(Customer).where(
            (Customer.phone_lookup_hmac == phone_hmac) |
            (Customer.email_lookup_hmac == email_hmac)
        )
    )

    cust = Customer(
        name=req.name.strip(),
        phone=req.phone.strip(),
        email=req.email.strip(),
        phone_encrypted=encrypt_aes_gcm(norm_phone),
        email_encrypted=encrypt_aes_gcm(norm_email),
        phone_lookup_hmac=phone_hmac,
        email_lookup_hmac=email_hmac,
        region=req.region,
        branch=req.branch or f"{req.region} Hub",
        source=req.source or "Website"
    )
    db.add(cust)
    db.flush()

    # Record DPDP Act Consent
    db.add(ConsentRecord(
        customer_id=cust.id,
        purpose=req.consent_purpose or "property_consultation",
        provenance="command_center_intake",
        notice_version="DPDP-2023-V1",
        consent_given=True,
        consent_given_at=now_utc()
    ))

    # Log operational activity & audit
    db.add(Activity(
        actor_id=current_user.id,
        actor_name=current_user.name,
        activity_type="customer.created",
        entity_type="customer",
        entity_id=cust.id,
        description=f"Customer '{cust.name}' created in {cust.region} (Duplicate status: {'Candidate' if existing else 'Unique'})",
        region=cust.region
    ))
    log_audit(db, current_user.id, "CUSTOMER_CREATED", f"id:{cust.id},region:{cust.region}", region=cust.region)
    db.commit()

    return {
        "status": "created",
        "customer_id": cust.id,
        "name": cust.name,
        "is_repeat_client": bool(existing),
        "existing_match_id": existing.id if existing else None
    }

@router.get("/leads")
def list_leads(
    region: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assignee_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = select(Lead)
    if current_user.role in REGION_SCOPE:
        q = q.where(Lead.region == current_user.region)
    elif current_user.role not in ALL_SCOPE:
        q = q.where(Lead.assignee_id == current_user.id)

    if region and (current_user.role in ALL_SCOPE or region == current_user.region):
        q = q.where(Lead.region == region)
    if status:
        q = q.where(Lead.status == status)
    if priority:
        q = q.where(Lead.priority == priority)
    if assignee_id:
        q = q.where(Lead.assignee_id == assignee_id)

    leads = db.scalars(q.order_by(desc(Lead.created_at)).limit(limit)).all()
    res = []
    for l in leads:
        cust = db.get(Customer, l.customer_id) if l.customer_id else None
        assignee = db.get(User, l.assignee_id) if l.assignee_id else None
        res.append({
            "id": l.id,
            "customer_id": l.customer_id,
            "customer_name": cust.name if cust else "Unknown",
            "project_id": l.project_id,
            "region": l.region,
            "branch": l.branch,
            "status": l.status,
            "priority": l.priority,
            "source": l.source,
            "budget": l.budget,
            "assignee_id": l.assignee_id,
            "assignee_name": assignee.name if assignee else "Unassigned",
            "created_at": l.created_at.isoformat() + "Z"
        })
    return res

@router.post("/leads")
def create_lead(
    req: LeadCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in PERMS["lead:write"]:
        raise HTTPException(status_code=403, detail="Not authorized to create leads.")

    lead = Lead(
        customer_id=req.customer_id,
        project_id=req.project_id,
        region=req.region,
        branch=req.branch,
        priority=req.priority or "normal",
        source=req.source or "Website",
        budget=req.budget or 10000000.0,
        assignee_id=req.assignee_id,
        crm_external_id=f"CRM-LD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )
    db.add(lead)
    db.flush()

    db.add(Activity(
        actor_id=current_user.id,
        actor_name=current_user.name,
        activity_type="lead.created",
        entity_type="lead",
        entity_id=lead.id,
        description=f"New Lead created for customer {req.customer_id[:8]} in {lead.region}",
        region=lead.region
    ))
    db.commit()
    return {"status": "created", "lead_id": lead.id}

@router.post("/assignments")
def assign_lead(
    req: AssignmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in PERMS["lead:assign"]:
        raise HTTPException(status_code=403, detail="Not authorized to allocate leads.")

    lead = db.get(Lead, req.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found.")

    target_user = db.get(User, req.employee_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Target employee not found.")

    prev_assignee = lead.assignee_id
    lead.assignee_id = target_user.id
    target_user.active_leads_count += 1
    
    # Sync with external CRM
    sync_ok, sync_msg = CRMAdapter.sync_lead_assignment(lead.id, target_user.id, target_user.email)

    # Activity log
    act = Activity(
        actor_id=current_user.id,
        actor_name=current_user.name,
        activity_type="lead.assigned",
        entity_type="lead",
        entity_id=lead.id,
        description=f"Lead {lead.id[:8]} assigned to {target_user.name} ({target_user.region})",
        region=lead.region
    )
    db.add(act)

    log_audit(
        db, current_user.id, "LEAD_ASSIGNED",
        f"lead:{lead.id},from:{prev_assignee},to:{target_user.id}",
        region=current_user.region
    )
    db.commit()

    return {
        "status": "assigned",
        "lead_id": lead.id,
        "assignee_id": target_user.id,
        "assignee_name": target_user.name,
        "crm_sync_status": sync_msg
    }

@router.get("/activities")
def list_activities(
    region: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = select(Activity)
    if current_user.role in REGION_SCOPE:
        q = q.where(Activity.region == current_user.region)
    elif current_user.role not in ALL_SCOPE:
        q = q.where(Activity.actor_id == current_user.id)
    
    if region and (current_user.role in ALL_SCOPE or region == current_user.region):
        q = q.where(Activity.region == region)

    acts = db.scalars(q.order_by(desc(Activity.created_at)).limit(limit)).all()
    return [
        {
            "id": a.id,
            "ts": a.created_at.isoformat() + "Z",
            "actor_id": a.actor_id,
            "actor_name": a.actor_name,
            "activity_type": a.activity_type,
            "entity_type": a.entity_type,
            "entity_id": a.entity_id,
            "description": a.description,
            "region": a.region
        } for a in acts
    ]

@router.post("/activities")
def create_activity(
    req: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    act = Activity(
        actor_id=current_user.id,
        actor_name=current_user.name,
        activity_type=req.activity_type,
        entity_type=req.entity_type,
        entity_id=req.entity_id,
        description=req.description,
        region=req.region or current_user.region
    )
    db.add(act)
    db.commit()
    db.refresh(act)
    return {"status": "recorded", "activity_id": act.id}

@router.get("/consent")
def list_consent_records(
    customer_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ("super_admin", "admin", "auditor", "management"):
        raise HTTPException(status_code=403, detail="Not authorized to inspect consent governance registers.")

    q = select(ConsentRecord)
    if customer_id:
        q = q.where(ConsentRecord.customer_id == customer_id)
    records = db.scalars(q.order_by(desc(ConsentRecord.consent_given_at)).limit(limit)).all()
    return [
        {
            "id": r.id,
            "customer_id": r.customer_id,
            "purpose": r.purpose,
            "provenance": r.provenance,
            "notice_version": r.notice_version,
            "consent_given": r.consent_given,
            "consent_given_at": r.consent_given_at.isoformat() + "Z"
        } for r in records
    ]
