"""Audit Log Model (Append-Only, Hash-Chained)."""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import utc_now

class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    region: Mapped[str] = mapped_column(String(40), default="", index=True)
    action: Mapped[str] = mapped_column(String(80), index=True)
    resource: Mapped[str] = mapped_column(String(120), default="")
    result: Mapped[str] = mapped_column(String(20), default="SUCCESS")
    ip_hash: Mapped[str] = mapped_column(String(32), default="")
    prev_hash: Mapped[str] = mapped_column(String(64))
    hash: Mapped[str] = mapped_column(String(64), index=True)
