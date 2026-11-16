"""Model package exports."""
from backend.app.models.base import Base
from backend.app.models.identity import User
from backend.app.models.organization import Region, Branch, Department
from backend.app.models.real_estate import Project, Property, Unit, Viewing
from backend.app.models.crm import Customer, Lead, Deal, Task, FollowUp
from backend.app.models.operations import AssignmentJob, AssignmentRecord, OperationalEvent
from backend.app.models.integration import Outbox, ProcessedEvent, ConflictLog
from backend.app.models.audit import AuditLog
from backend.app.models.dashboards import Dashboard, DashboardWidget, SavedView, UserPreference
from backend.app.models.agents import AgentExecution, AgentToolCall, AgentProposal

__all__ = [
    "Base",
    "User",
    "Region",
    "Branch",
    "Department",
    "Project",
    "Property",
    "Unit",
    "Viewing",
    "Customer",
    "Lead",
    "Deal",
    "Task",
    "FollowUp",
    "AssignmentJob",
    "AssignmentRecord",
    "OperationalEvent",
    "Outbox",
    "ProcessedEvent",
    "ConflictLog",
    "AuditLog",
    "Dashboard",
    "DashboardWidget",
    "SavedView",
    "UserPreference",
    "AgentExecution",
    "AgentToolCall",
    "AgentProposal"
]
