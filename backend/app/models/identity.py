"""Identity, Users, Roles, and Authentication Models."""
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import generate_uuid, utc_now

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
