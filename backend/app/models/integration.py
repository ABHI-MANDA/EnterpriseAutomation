"""Integration Models: Transactional Outbox, Inbound Webhook Idempotency, and Conflict Log."""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import generate_uuid, utc_now

class Outbox(Base):
    __tablename__ = "outbox"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    event: Mapped[str] = mapped_column(String(80), index=True)
    payload: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)  # pending, sent, failed
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    event_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    source: Mapped[str] = mapped_column(String(40), default="crm")
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class ConflictLog(Base):
    __tablename__ = "conflict_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    entity_type: Mapped[str] = mapped_column(String(40), index=True)
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    central_value: Mapped[str] = mapped_column(Text)
    crm_value: Mapped[str] = mapped_column(Text)
    resolution: Mapped[str] = mapped_column(String(40), default="unresolved")  # crm_wins, central_wins, manual_review, unresolved
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
