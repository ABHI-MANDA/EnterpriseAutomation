"""Dashboard Engine Models: Dynamic Widgets, Layouts, Preferences, and Saved Views."""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base
from backend.app.models.base import generate_uuid, utc_now

class Dashboard(Base):
    __tablename__ = "dashboards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(120))
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    role_target: Mapped[str | None] = mapped_column(String(40), nullable=True)  # e.g. super_admin, regional_manager
    layout_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    dashboard_id: Mapped[str] = mapped_column(String(36), ForeignKey("dashboards.id"), index=True)
    widget_type: Mapped[str] = mapped_column(String(50))  # kpi, line_chart, bar_chart, pie_chart, funnel, activity_feed, table
    metric_key: Mapped[str] = mapped_column(String(60))  # e.g. total_leads, conversion_rate, pipeline_value
    title: Mapped[str] = mapped_column(String(100))
    position_json: Mapped[str] = mapped_column(String(255), default='{"x": 0, "y": 0, "w": 3, "h": 2}')
    config_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class SavedView(Base):
    __tablename__ = "saved_views"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    module: Mapped[str] = mapped_column(String(40), index=True)  # leads, customers, projects, inventory, tasks
    title: Mapped[str] = mapped_column(String(100))
    filters_json: Mapped[str] = mapped_column(Text, default="{}")
    columns_json: Mapped[str] = mapped_column(Text, default="[]")
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, index=True)
    active_dashboard_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    theme: Mapped[str] = mapped_column(String(20), default="light")
    preferences_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
