"""Real Estate Domain Models: Projects, Properties, Units, Viewings."""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import generate_uuid, utc_now

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(150), index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    region: Mapped[str] = mapped_column(String(40), index=True)
    branch: Mapped[str] = mapped_column(String(60), default="")
    project_type: Mapped[str] = mapped_column(String(40), default="Residential")  # Residential, Commercial, Mixed
    status: Mapped[str] = mapped_column(String(30), default="Active")  # Active, Planning, Completed
    total_units: Mapped[int] = mapped_column(Integer, default=0)
    launch_date: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class Property(Base):
    __tablename__ = "properties"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))  # e.g. Tower A, Phase 1, Villa Enclave
    total_floors: Mapped[int] = mapped_column(Integer, default=1)
    region: Mapped[str] = mapped_column(String(40), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class Unit(Base):
    __tablename__ = "units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), index=True)
    property_id: Mapped[str] = mapped_column(String(36), ForeignKey("properties.id"), index=True)
    unit_number: Mapped[str] = mapped_column(String(40), index=True)
    bhk: Mapped[str] = mapped_column(String(20), default="3 BHK")  # 1 BHK, 2 BHK, 3 BHK, 4 BHK, Penthouse
    area_sqft: Mapped[float] = mapped_column(Float, default=1200.0)
    price: Mapped[float] = mapped_column(Float, default=15000000.0)
    status: Mapped[str] = mapped_column(String(30), default="available", index=True)  # available, reserved, sold
    region: Mapped[str] = mapped_column(String(40), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class Viewing(Base):
    __tablename__ = "viewings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    unit_id: Mapped[str] = mapped_column(String(36), ForeignKey("units.id"), index=True)
    lead_id: Mapped[str] = mapped_column(String(36), index=True)
    employee_id: Mapped[str] = mapped_column(String(36), index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(30), default="scheduled")  # scheduled, completed, cancelled
    feedback: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
