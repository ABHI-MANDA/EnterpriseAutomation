"""CRM Models: Customers, Leads, Deals, Tasks, Follow-ups."""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import generate_uuid, utc_now

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str] = mapped_column(String(200), index=True)
    phone: Mapped[str] = mapped_column(String(30))
    region: Mapped[str] = mapped_column(String(40), index=True)
    branch: Mapped[str] = mapped_column(String(60), default="")
    source: Mapped[str] = mapped_column(String(50), default="Website", index=True)
    assignee_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    project_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("projects.id"), nullable=True, index=True)
    region: Mapped[str] = mapped_column(String(40), index=True)
    branch: Mapped[str] = mapped_column(String(60), default="")
    status: Mapped[str] = mapped_column(String(30), default="new", index=True)  # new, contacted, qualified, negotiation, won, lost
    priority: Mapped[str] = mapped_column(String(20), default="normal", index=True)  # urgent, high, normal, low
    source: Mapped[str] = mapped_column(String(50), default="Website", index=True)
    budget: Mapped[float] = mapped_column(Float, default=10000000.0)
    assignee_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    crm_external_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    first_response_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id"), index=True)
    unit_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("units.id"), nullable=True, index=True)
    deal_value: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(30), default="proposal", index=True)  # proposal, negotiation, closed_won, closed_lost
    region: Mapped[str] = mapped_column(String(40), index=True)
    expected_close_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    lead_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    assignee_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    region: Mapped[str] = mapped_column(String(40), index=True)
    priority: Mapped[str] = mapped_column(String(20), default="normal")  # urgent, high, normal, low
    due: Mapped[datetime] = mapped_column(DateTime, index=True)
    done_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class FollowUp(Base):
    __tablename__ = "followups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    lead_id: Mapped[str] = mapped_column(String(36), ForeignKey("leads.id"), index=True)
    employee_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    region: Mapped[str] = mapped_column(String(40), index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    outcome: Mapped[str] = mapped_column(String(60), default="pending")  # completed, rescheduled, no_answer, positive
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
