"""Organization & Geographic Hierarchy Models: Regions, Branches, Departments, Cities, Zones, Localities."""
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import generate_uuid, utc_now

class Region(Base):
    __tablename__ = "regions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(10), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), index=True)
    region_id: Mapped[str] = mapped_column(String(36), index=True)
    code: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class Department(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

# --- Location Master Tables (City, Zone, Locality) ---

class City(Base):
    """City Master Table for standardized geographic mapping."""
    __tablename__ = "cities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # e.g. Bengaluru, Mumbai, Delhi NCR, Hyderabad
    state: Mapped[str] = mapped_column(String(100), default="Karnataka")
    country: Mapped[str] = mapped_column(String(60), default="India")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class Zone(Base):
    """Zone Master Table (South, North, East, West, Central)."""
    __tablename__ = "zones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(60), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class Locality(Base):
    """Locality Master Table linked to City and Zone."""
    __tablename__ = "localities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(120), index=True)  # e.g. Whitefield, Indiranagar, HSR Layout, Cyber City
    city_id: Mapped[str] = mapped_column(String(36), ForeignKey("cities.id"), index=True)
    zone_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("zones.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
