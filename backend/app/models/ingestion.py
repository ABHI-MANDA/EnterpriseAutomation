"""Data Ingestion, Staging, Validation, and Deduplication Engine Models."""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import generate_uuid, utc_now

class ImportBatch(Base):
    """Tracks bulk ingestion runs (up to 800,000+ records) with checksum & reconciliation."""
    __tablename__ = "import_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    source_filename: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(50), default="CSV")  # CSV, XLSX, CRM_SYNC
    uploaded_by: Mapped[str] = mapped_column(String(36), index=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    
    # Reconciliation Counters
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    valid_records: Mapped[int] = mapped_column(Integer, default=0)
    successful_records: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_candidates: Mapped[int] = mapped_column(Integer, default=0)
    rejected_records: Mapped[int] = mapped_column(Integer, default=0)
    missing_mobile: Mapped[int] = mapped_column(Integer, default=0)
    invalid_emails: Mapped[int] = mapped_column(Integer, default=0)
    unmatched_projects_count: Mapped[int] = mapped_column(Integer, default=0)
    unmatched_locations_count: Mapped[int] = mapped_column(Integer, default=0)
    
    file_checksum: Mapped[str] = mapped_column(String(64), index=True)  # SHA-256
    batch_status: Mapped[str] = mapped_column(String(30), default="completed", index=True)  # uploaded, validating, staging, completed, failed
    error_summary: Mapped[str] = mapped_column(Text, default="[]")
    quality_report_json: Mapped[str] = mapped_column(Text, default="{}")

class DuplicateCandidate(Base):
    """Identified duplicate candidate flagged for deterministic review."""
    __tablename__ = "duplicate_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("import_batches.id"), index=True)
    existing_customer_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    incoming_name: Mapped[str] = mapped_column(String(120))
    incoming_phone_masked: Mapped[str] = mapped_column(String(30))
    incoming_email_masked: Mapped[str] = mapped_column(String(120))
    phone_lookup_hmac: Mapped[str] = mapped_column(String(64), index=True)
    email_lookup_hmac: Mapped[str] = mapped_column(String(64), index=True)
    match_reason: Mapped[str] = mapped_column(String(100))  # exact_mobile_hmac, exact_email_hmac, name_and_phone
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    status: Mapped[str] = mapped_column(String(30), default="pending_review", index=True)  # pending_review, merged, kept_separate, rejected
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class DuplicateResolution(Base):
    """Historical audit record of deduplication decisions."""
    __tablename__ = "duplicate_resolutions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("duplicate_candidates.id"), index=True)
    resolution_action: Mapped[str] = mapped_column(String(50))  # merge, keep_separate, reject
    resolved_by: Mapped[str] = mapped_column(String(36), index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    resolved_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class UnmatchedEntity(Base):
    """Staging table for unmatched Project or Locality names requiring administrative review."""
    __tablename__ = "unmatched_entities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    batch_id: Mapped[str] = mapped_column(String(36), ForeignKey("import_batches.id"), index=True)
    entity_type: Mapped[str] = mapped_column(String(40), index=True)  # project, locality, city, property_type
    raw_value: Mapped[str] = mapped_column(String(150), index=True)
    suggested_match: Mapped[str | None] = mapped_column(String(150), nullable=True)
    context_info: Mapped[str | None] = mapped_column(Text, nullable=True)       # JSON with extra context (row count, sample rows)
    resolution_status: Mapped[str] = mapped_column(String(30), default="pending", index=True)  # pending, mapped, ignored
    resolved_to_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)  # FK to resolved entity
    # Legacy alias kept for backward compat
    status: Mapped[str] = mapped_column(String(30), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
