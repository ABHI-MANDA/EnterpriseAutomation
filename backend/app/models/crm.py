"""CRM Models: Customers, Leads, Deals, Tasks, Follow-ups, Communications, Activities, and Consent."""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import generate_uuid, utc_now

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(120), index=True)
    email: Mapped[str] = mapped_column(String(200), index=True)
    phone: Mapped[str] = mapped_column(String(30))
    # Encrypted fields for data privacy & compliance (AES-256-GCM)
    email_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Deterministic HMAC-SHA-256 for zero-knowledge deduplication lookup
    email_lookup_hmac: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    phone_lookup_hmac: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    
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

class Activity(Base):
    """User and system operational business activities."""
    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    actor_id: Mapped[str] = mapped_column(String(36), index=True)
    actor_name: Mapped[str] = mapped_column(String(120), default="")
    activity_type: Mapped[str] = mapped_column(String(60), index=True)  # lead.created, task.completed, crm.sync, deal.updated
    entity_type: Mapped[str] = mapped_column(String(40), index=True)  # lead, task, customer, deal
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    description: Mapped[str] = mapped_column(String(255))
    region: Mapped[str] = mapped_column(String(40), default="", index=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)

class Communication(Base):
    """Customer interaction logs: calls, emails, messages."""
    __tablename__ = "communications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    lead_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    sender_id: Mapped[str] = mapped_column(String(36), index=True)
    channel: Mapped[str] = mapped_column(String(30))  # phone_call, email, whatsapp, meeting
    direction: Mapped[str] = mapped_column(String(20), default="outbound")  # inbound, outbound
    summary: Mapped[str] = mapped_column(Text)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class ConsentRecord(Base):
    """DPDP Act (Digital Personal Data Protection Act, 2023) Consent Register."""
    __tablename__ = "consent_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(120))  # property_consultation, direct_marketing, site_visit
    provenance: Mapped[str] = mapped_column(String(120))  # web_form, verified_call, site_registration
    notice_version: Mapped[str] = mapped_column(String(20), default="DPDP-2023-V1")
    consent_given: Mapped[bool] = mapped_column(Boolean, default=True)
    consent_given_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    withdrawn_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    channel_ip_hash: Mapped[str] = mapped_column(String(64), default="")
