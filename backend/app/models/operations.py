"""Operations Models: Bulk Assignment Jobs, Per-record Tracking, and Events."""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import generate_uuid, utc_now

class AssignmentJob(Base):
    __tablename__ = "assignment_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    batch_id: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    created_by: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(30), default="preview", index=True)  # preview, approved, rejected, completed, partial_failure
    total_leads: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class AssignmentRecord(Base):
    __tablename__ = "assignment_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("assignment_jobs.id"), index=True)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id"), index=True)
    recommended_assignee_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    final_assignee_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, success, failed
    crm_sync_status: Mapped[str] = mapped_column(String(30), default="pending")  # pending, success, failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class OperationalEvent(Base):
    __tablename__ = "operational_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    actor_name: Mapped[str] = mapped_column(String(120))
    target_type: Mapped[str] = mapped_column(String(40))
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    action_desc: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="completed")
    crm_sync_status: Mapped[str] = mapped_column(String(30), default="success")
    correlation_id: Mapped[str] = mapped_column(String(60), index=True)
    payload: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
