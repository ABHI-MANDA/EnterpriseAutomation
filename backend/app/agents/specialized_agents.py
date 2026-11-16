"""Specialized AI Agents implementations."""
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.identity import User
from backend.app.agents.tools import GovernedAgentTools

class DataQueryAgent:
    """Interprets natural language questions and retrieves authorized records with exact evidence."""
    @staticmethod
    def handle(db: Session, current_user: User, text: str, context_filters: Dict[str, Any] | None = None) -> Dict[str, Any]:
        text_lower = text.lower()
        region = context_filters.get("region") if context_filters else None
        
        # Region extraction
        for r in ["south", "north", "west", "east"]:
            if r in text_lower:
                region = r.capitalize()

        unassigned = "unassigned" in text_lower or "without owner" in text_lower
        status = None
        for s in ["new", "contacted", "qualified", "negotiation", "won", "lost"]:
            if s in text_lower:
                status = s
                break

        res = GovernedAgentTools.query_leads(
            db=db,
            current_user=current_user,
            region=region,
            status=status,
            unassigned_only=unassigned,
            limit=10
        )

        records = res.get("items", [])
        data_points = [
            f"Lead {r['id'][:8]}: {r['customer_name']} | Status: {r['status']} | Region: {r['region']} | Assignee: {r['assignee_name']}"
            for r in records
        ]

        summary_msg = f"Found {res.get('total', 0)} matching lead records"
        if region:
            summary_msg += f" in {region} region"
        if unassigned:
            summary_msg += " that are currently unassigned"
        summary_msg += "."

        return {
            "agent_name": "Data Query Agent",
            "message": summary_msg,
            "interpreted_filters": {"region": region, "status": status, "unassigned": unassigned},
            "evidence": [{
                "title": f"Authorized Lead Records ({len(records)} shown)",
                "data_points": data_points if data_points else ["No records matching criteria within your authorized scope."],
                "supporting_record_ids": [r["id"] for r in records]
            }]
        }

class BusinessInsightAgent:
    """Analyzes conversions, project performance, and regional bottlenecks."""
    @staticmethod
    def handle(db: Session, current_user: User, text: str, context_filters: Dict[str, Any] | None = None) -> Dict[str, Any]:
        region = context_filters.get("region") if context_filters else None
        sales_intel = GovernedAgentTools.get_sales_intelligence(db, current_user, region)
        proj_perf = sales_intel.get("project_performance", [])

        # Sort projects by conversion rate
        sorted_projects = sorted(proj_perf, key=lambda p: p["conversion_rate"], reverse=True)
        best = sorted_projects[0] if sorted_projects else None
        worst = sorted_projects[-1] if len(sorted_projects) > 1 else None

        data_points = []
        if best:
            data_points.append(f"Top Performing: {best['project_name']} ({best['region']}) with {best['conversion_rate']}% conversion rate ({best['deals_count']} closed deals).")
        if worst and worst != best:
            data_points.append(f"Requires Attention: {worst['project_name']} ({worst['region']}) with {worst['conversion_rate']}% conversion rate ({worst['leads_count']} total leads).")

        return {
            "agent_name": "Business Insight Agent",
            "message": f"Conversion analysis reveals {best['project_name'] if best else 'Active Portfolio'} is delivering the strongest sales conversion.",
            "evidence": [{
                "title": "Project Performance Intelligence",
                "data_points": data_points,
                "supporting_record_ids": [p["project_id"] for p in sorted_projects[:3]]
            }]
        }

class WorkloadOptimizationAgent:
    """Evaluates employee capacity and recommends lead allocations."""
    @staticmethod
    def handle(db: Session, current_user: User, text: str, context_filters: Dict[str, Any] | None = None) -> Dict[str, Any]:
        region = context_filters.get("region") if context_filters else None
        unassigned_res = GovernedAgentTools.query_leads(
            db=db,
            current_user=current_user,
            region=region,
            unassigned_only=True,
            limit=5
        )
        unassigned_leads = unassigned_res.get("items", [])

        if not unassigned_leads:
            return {
                "agent_name": "Workload Optimization Agent",
                "message": "All current leads within your authorized region are already allocated. No pending unassigned leads detected.",
                "evidence": []
            }

        lead_ids = [l["id"] for l in unassigned_leads]
        allocations = GovernedAgentTools.propose_lead_allocation(db, current_user, lead_ids)

        evidence_points = [
            f"Lead {a['customer_name']} -> Recommended: {a['recommended_assignee_name']} (Reason: {a['reason']}, Current Workload: {a['current_workload']})"
            for a in allocations
        ]

        return {
            "agent_name": "Workload Optimization Agent",
            "message": f"Prepared an allocation plan for {len(allocations)} unassigned leads based on capacity, region, and project specialization.",
            "evidence": [{
                "title": "Workload Optimization Plan (Requires Manager Approval)",
                "data_points": evidence_points,
                "supporting_record_ids": lead_ids
            }],
            "proposed_action": {
                "action_type": "lead_assignment",
                "summary": f"Approve allocation of {len(allocations)} leads to recommended sales executives",
                "details": {
                    "lead_ids": lead_ids,
                    "allocations": allocations
                },
                "requires_approval": True
            }
        }

class MonitoringAgent:
    """Tracks operations, CRM synchronization latency, and failures."""
    @staticmethod
    def handle(db: Session, current_user: User, text: str) -> Dict[str, Any]:
        overview = GovernedAgentTools.get_overview_metrics(db, current_user)
        health = overview.get("crm_sync_health", "Healthy")
        alerts = overview.get("security_alerts_7d", 0)

        points = [
            f"CRM Bidirectional Sync Engine: Status is {health}.",
            f"Pending Follow-ups Across Portfolio: {overview.get('pending_followups', 0)}.",
            f"Overdue Tasks Requiring Attention: {overview.get('overdue_tasks', 0)}.",
            f"Security & Audit Alerts (Last 7 Days): {alerts}."
        ]

        return {
            "agent_name": "Monitoring Agent",
            "message": f"System operational health is currently {health}. {overview.get('overdue_tasks', 0)} tasks are currently overdue.",
            "evidence": [{
                "title": "Operational Health Monitor",
                "data_points": points,
                "supporting_record_ids": []
            }]
        }

class RiskAnomalyAgent:
    """Detects unusual access, lead distribution spikes, and operational anomalies."""
    @staticmethod
    def handle(db: Session, current_user: User, text: str) -> Dict[str, Any]:
        workloads = GovernedAgentTools.get_employee_workload(db, current_user)
        overloaded = [w for w in workloads if w.get("overloaded")]

        data_points = []
        if overloaded:
            for o in overloaded:
                data_points.append(f"Workload Disproportion: {o['name']} ({o['region']}) is carrying {o['assigned_leads']} leads and {o['open_tasks']} open tasks.")
        else:
            data_points.append("Lead distribution is balanced across all active sales personnel.")

        return {
            "agent_name": "Risk & Anomaly Agent",
            "message": f"Identified {len(overloaded)} employees with workload disproportion exceeding threshold rules." if overloaded else "No operational anomalies detected.",
            "evidence": [{
                "title": "Operational Risk & Anomaly Assessment",
                "data_points": data_points,
                "supporting_record_ids": [o["employee_id"] for o in overloaded]
            }]
        }
