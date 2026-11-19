"""Identity, Users, Roles, Permissions, and Access Log Models."""
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import generate_uuid, utc_now

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(200), default="")

class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    module: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[str] = mapped_column(String(200), default="")

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    pw_hash: Mapped[str] = mapped_column(String(200))
    role: Mapped[str] = mapped_column(String(40), index=True)
    department: Mapped[str] = mapped_column(String(60), default="Sales")
    region: Mapped[str] = mapped_column(String(40), default="", index=True)
    branch: Mapped[str] = mapped_column(String(60), default="")
    expertise: Mapped[str] = mapped_column(String(255), default="Luxury, Residential")  # Comma separated tags
    active_leads_count: Mapped[int] = mapped_column(Integer, default=0)
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    fails: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class AccessLog(Base):
    """Tracks accessibility intelligence: period, region, and security compliance."""
    __tablename__ = "access_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    ts: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    user_email: Mapped[str] = mapped_column(String(200), default="")
    user_role: Mapped[str] = mapped_column(String(40), default="")
    assigned_region: Mapped[str] = mapped_column(String(40), default="", index=True)
    target_region: Mapped[str] = mapped_column(String(40), default="", index=True)
    resource_type: Mapped[str] = mapped_column(String(50), default="dashboard")
    action_type: Mapped[str] = mapped_column(String(50), default="view")
    status: Mapped[str] = mapped_column(String(30), default="AUTHORIZED", index=True)  # AUTHORIZED, CROSS_REGION_DENIED, UNAUTHORIZED, SUSPICIOUS_HOURS
    ip_hash: Mapped[str] = mapped_column(String(32), default="")
