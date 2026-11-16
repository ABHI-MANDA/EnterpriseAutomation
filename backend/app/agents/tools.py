"""Governed Backend Tool Registry for AI Agents.
All tools are strictly permission-checked and mapped to deterministic backend services.
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.identity import User
from backend.app.services.analytics_service import get_executive_overview, get_sales_intelligence, get_employee_operations
from backend.app.services.record_service import query_records_paginated
from backend.app.services.workload_service import evaluate_lead_allocations

class GovernedAgentTools:
    @staticmethod
    def get_overview_metrics(db: Session, current_user: User, region: Optional[str] = None) -> Dict[str, Any]:
        """Tool: Fetch canonical executive overview metrics."""
        return get_executive_overview(db, current_user, region)

    @staticmethod
    def get_sales_intelligence(db: Session, current_user: User, region: Optional[str] = None) -> Dict[str, Any]:
        """Tool: Fetch sales funnel, project conversions, and monthly trends."""
        return get_sales_intelligence(db, current_user, region)

    @staticmethod
    def get_employee_workload(db: Session, current_user: User, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """Tool: Retrieve employee task workload and capacity statistics."""
        return get_employee_operations(db, current_user, region)

    @staticmethod
    def query_leads(
        db: Session,
        current_user: User,
        region: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        unassigned_only: bool = False,
        limit: int = 15
    ) -> Dict[str, Any]:
        """Tool: Retrieve authorized leads matching structured filters."""
        filters = {}
        if region:
            filters["region"] = region
        if status:
            filters["status"] = status
        if priority:
            filters["priority"] = priority
        if unassigned_only:
            filters["unassigned"] = True

        return query_records_paginated(
            db=db,
            module="leads",
            page=1,
            limit=limit,
            filters=filters,
            current_user=current_user
        )

    @staticmethod
    def propose_lead_allocation(
        db: Session,
        current_user: User,
        lead_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Tool: Evaluate workload & allocation criteria and propose sales executive assignments."""
        return evaluate_lead_allocations(db, lead_ids, current_user)
