"""Model package exports."""
from backend.app.models.base import Base
from backend.app.models.identity import User, Role, Permission, AccessLog
from backend.app.models.organization import Region, Branch, Department, City, Zone, Locality
from backend.app.models.real_estate import Project, Property, Unit, Viewing, PropertyType
from backend.app.models.crm import (
    Customer, Lead, Deal, Task, FollowUp, Activity, Communication, ConsentRecord, LeadAllocation
)
from backend.app.models.operations import AssignmentJob, AssignmentRecord, OperationalEvent
from backend.app.models.integration import Outbox, ProcessedEvent, ConflictLog
from backend.app.models.audit import AuditLog
from backend.app.models.dashboards import Dashboard, DashboardWidget, SavedView, UserPreference
from backend.app.models.agents import AgentExecution, AgentToolCall, AgentProposal
from backend.app.models.ingestion import ImportBatch, DuplicateCandidate, DuplicateResolution, UnmatchedEntity

__all__ = [
    "Base",
    "User",
    "Role",
    "Permission",
    "AccessLog",
    "Region",
    "Branch",
    "Department",
    "City",
    "Zone",
    "Locality",
    "Project",
    "Property",
    "Unit",
    "Viewing",
    "PropertyType",
    "Customer",
    "Lead",
    "LeadAllocation",
    "Deal",
    "Task",
    "FollowUp",
    "Activity",
    "Communication",
    "ConsentRecord",
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
    "AgentProposal",
    "ImportBatch",
    "DuplicateCandidate",
    "DuplicateResolution",
    "UnmatchedEntity"
]
