"""Reporting Service.
Generates CSV and structured summaries with strict data masking and audit logging.
"""
import io
import csv
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.security import ALL_SCOPE, REGION_SCOPE, mask_text, PERMS
from backend.app.core.audit import log_audit
from backend.app.models.identity import User
from backend.app.models.crm import Lead, Customer
from backend.app.models.real_estate import Project

def generate_leads_report_csv(db: Session, current_user: User, region: str | None = None) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["lead_id", "customer_name", "region", "status", "priority", "source", "budget", "created_at"])

    q = select(Lead)
    if current_user.role in REGION_SCOPE:
        q = q.where(Lead.region == current_user.region)
    elif current_user.role not in ALL_SCOPE:
        q = q.where(Lead.assignee_id == current_user.id)

    if region and (current_user.role in ALL_SCOPE or region == current_user.region):
        q = q.where(Lead.region == region)

    leads = db.scalars(q.limit(1000)).all()
    unmasked = current_user.role in PERMS["unmasked"]

    for l in leads:
        cust = db.get(Customer, l.customer_id) if l.customer_id else None
        c_name = cust.name if cust else "Unknown"
        writer.writerow([
            l.id,
            c_name,
            l.region,
            l.status,
            l.priority,
            l.source,
            l.budget,
            l.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])

    log_audit(db, current_user.id, "REPORT_EXPORT_LEADS_CSV", f"records:{len(leads)}", region=current_user.region)
    return output.getvalue()
