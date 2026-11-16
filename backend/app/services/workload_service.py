"""Workload Optimization Service.
Evaluates team capacity, lead priority, project familiarity, and allocation rules
to produce explainable assignment recommendations.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from backend.app.models.identity import User
from backend.app.models.crm import Lead, Task
from backend.app.models.real_estate import Project

def evaluate_lead_allocations(
    db: Session,
    lead_ids: List[str],
    current_user: User
) -> List[Dict[str, Any]]:
    # Retrieve leads
    leads = db.scalars(select(Lead).where(Lead.id.in_(lead_ids))).all()
    if not leads:
        return []

    # Get active sales executives in applicable regions
    regions = list({l.region for l in leads if l.region})
    eq = select(User).where(User.active == True, User.role.in_(["employee", "regional_manager"]))
    if current_user.role not in ("super_admin", "admin", "management"):
        eq = eq.where(User.region == current_user.region)
    elif regions:
        eq = eq.where(User.region.in_(regions))
    
    executives = db.scalars(eq).all()
    if not executives:
        # Fallback to all active employees
        executives = db.scalars(select(User).where(User.active == True, User.role == "employee")).all()

    # Pre-fetch workloads
    workload_map = {}
    for exec_user in executives:
        active_cnt = db.scalar(select(func.count(Lead.id)).where(Lead.assignee_id == exec_user.id, Lead.status.notin_(["won", "lost"]))) or 0
        pending_tasks = db.scalar(select(func.count(Task.id)).where(Task.assignee_id == exec_user.id, Task.done_at.is_(None))) or 0
        won_cnt = db.scalar(select(func.count(Lead.id)).where(Lead.assignee_id == exec_user.id, Lead.status == "won")) or 0
        total_assigned = db.scalar(select(func.count(Lead.id)).where(Lead.assignee_id == exec_user.id)) or 1
        conversion_rate = won_cnt / total_assigned

        workload_map[exec_user.id] = {
            "user": exec_user,
            "active_leads": active_cnt,
            "pending_tasks": pending_tasks,
            "conversion_rate": conversion_rate,
            "allocated_in_batch": 0
        }

    recommendations = []
    for lead in leads:
        # Find best candidate
        best_exec_id = None
        best_score = -999999.0
        reasons = []

        # Candidate pool matching region
        candidates = [e for e in executives if not lead.region or e.region == lead.region]
        if not candidates:
            candidates = executives

        for cand in candidates:
            stats = workload_map[cand.id]
            current_load = stats["active_leads"] + stats["allocated_in_batch"]

            # Heuristic scoring
            score = 100.0
            cand_reasons = []

            # 1. Region match
            if cand.region == lead.region:
                score += 40.0
                cand_reasons.append("Regional match")
            
            # 2. Workload penalty
            load_penalty = current_load * 3.0
            score -= load_penalty
            if current_load < 10:
                cand_reasons.append("lower workload")
            
            # 3. High priority lead requires proven closer
            if lead.priority in ("urgent", "high"):
                score += stats["conversion_rate"] * 50.0
                if stats["conversion_rate"] > 0.15:
                    cand_reasons.append("high conversion record")

            # 4. Project specialization
            if cand.expertise and "Luxury" in cand.expertise and (lead.budget or 0) > 20000000:
                score += 30.0
                cand_reasons.append("luxury project specialization")

            if score > best_score:
                best_score = score
                best_exec_id = cand.id
                reasons = cand_reasons

        selected_id = best_exec_id or executives[0].id
        selected_user = workload_map[selected_id]["user"]
        workload_map[selected_id]["allocated_in_batch"] += 1

        lead_customer_name = "Customer"
        if lead.customer_id:
            from backend.app.models.crm import Customer
            cust = db.get(Customer, lead.customer_id)
            if cust:
                lead_customer_name = cust.name

        project_name = "General Portfolio"
        if lead.project_id:
            proj = db.get(Project, lead.project_id)
            if proj:
                project_name = proj.name

        final_reason = ", ".join(reasons) if reasons else "Balanced capacity allocation"
        recommendations.append({
            "lead_id": lead.id,
            "customer_name": lead_customer_name,
            "region": lead.region,
            "project_name": project_name,
            "recommended_assignee_id": selected_user.id,
            "recommended_assignee_name": selected_user.name,
            "reason": final_reason,
            "current_workload": workload_map[selected_id]["active_leads"] + workload_map[selected_id]["allocated_in_batch"]
        })

    return recommendations
