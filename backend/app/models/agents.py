"""AI Agent Governance Models: Executions, Tool Calls, Proposals & Approvals."""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import generate_uuid, utc_now

class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(60), index=True)
    request_text: Mapped[str] = mapped_column(Text)
    intent: Mapped[str] = mapped_column(String(40), index=True)  # query, analysis, recommendation, action, monitoring
    status: Mapped[str] = mapped_column(String(30), default="completed")  # started, completed, failed, waiting_approval
    result_summary: Mapped[str] = mapped_column(Text, default="")
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class AgentToolCall(Base):
    __tablename__ = "agent_tool_calls"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_executions.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String(80))
    input_json: Mapped[str] = mapped_column(Text, default="{}")
    output_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(20), default="success")  # success, error
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class AgentProposal(Base):
    __tablename__ = "agent_proposals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("agent_executions.id"), index=True)
    proposal_type: Mapped[str] = mapped_column(String(50))  # lead_assignment, task_generation, followup_schedule
    payload_json: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="pending_review", index=True)  # pending_review, approved, rejected, executed
    approved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
