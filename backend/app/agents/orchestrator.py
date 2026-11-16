"""Master AI Agent Orchestrator.
Coordinates intent classification, dispatches to specialized agents,
enforces authorization perimeters, and logs execution lifecycle.
"""
import time
import uuid
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.core.security import now_utc
from backend.app.models.identity import User
from backend.app.models.agents import AgentExecution
from backend.app.agents.specialized_agents import (
    DataQueryAgent,
    BusinessInsightAgent,
    WorkloadOptimizationAgent,
    MonitoringAgent,
    RiskAnomalyAgent
)

class MasterOrchestrator:
    @staticmethod
    def process_request(
        db: Session,
        current_user: User,
        user_message: str,
        context_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        msg_lower = user_message.lower().strip()
        execution_id = "EXEC-" + uuid.uuid4().hex[:12].upper()

        # 1. Intent Classification
        if any(w in msg_lower for w in ["recommend", "allocate", "assign", "workload", "capacity"]):
            intent = "action"
            agent_result = WorkloadOptimizationAgent.handle(db, current_user, user_message, context_filters)
        elif any(w in msg_lower for w in ["convert", "conversion", "highest", "lowest", "trend", "insight", "best", "worst"]):
            intent = "analysis"
            agent_result = BusinessInsightAgent.handle(db, current_user, user_message, context_filters)
        elif any(w in msg_lower for w in ["monitor", "health", "sync", "failed", "status", "alert"]):
            intent = "monitoring"
            agent_result = MonitoringAgent.handle(db, current_user, user_message)
        elif any(w in msg_lower for w in ["risk", "anomaly", "overload", "unusual", "pattern"]):
            intent = "analysis"
            agent_result = RiskAnomalyAgent.handle(db, current_user, user_message)
        else:
            intent = "query"
            agent_result = DataQueryAgent.handle(db, current_user, user_message, context_filters)

        elapsed_ms = int((time.time() - start_time) * 1000)

        # 2. Record Agent Execution Audit
        exec_record = AgentExecution(
            id=execution_id,
            user_id=current_user.id,
            agent_name=agent_result.get("agent_name", "Master Orchestrator"),
            request_text=user_message,
            intent=intent,
            status="completed",
            result_summary=agent_result.get("message", "")[:250],
            execution_time_ms=elapsed_ms
        )
        db.add(exec_record)
        db.commit()

        # 3. Assemble Consolidated Response
        return {
            "execution_id": execution_id,
            "agent_name": agent_result.get("agent_name", "Master Orchestrator"),
            "intent": intent,
            "message": agent_result.get("message", "Request completed."),
            "interpreted_filters": agent_result.get("interpreted_filters"),
            "evidence": agent_result.get("evidence", []),
            "proposed_action": agent_result.get("proposed_action"),
            "execution_status": "success"
        }
