"""Comprehensive Automated Test Suite for Real Estate Command Center Platform."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.core.security import hash_pw, check_pw, create_access_token, decode_access_token
from backend.app.core.audit import log_audit, verify_audit_chain
from backend.app.models.identity import User
from backend.app.models.crm import Lead, Customer
from backend.app.models.real_estate import Project
from backend.app.services.seed_service import seed_database
from backend.app.services.analytics_service import get_executive_overview, get_sales_intelligence
from backend.app.services.workload_service import evaluate_lead_allocations
from backend.app.services.assignment_service import AssignmentService
from backend.app.services.record_service import query_records_paginated
from backend.app.agents.orchestrator import MasterOrchestrator

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    seed_database(session)
    yield session
    session.close()

def test_password_hashing():
    pw = "SecretPass123!"
    hashed = hash_pw(pw)
    assert check_pw(pw, hashed) is True
    assert check_pw("WrongPass", hashed) is False

def test_jwt_token_generation():
    token = create_access_token("user-123", "management", "South")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "management"
    assert payload["region"] == "South"

def test_audit_hash_chain_integrity(test_db):
    # Verify current chain is intact
    intact, broken_id = verify_audit_chain(test_db)
    assert intact is True
    assert broken_id is None

    # Add a new audit log
    log_audit(test_db, "user-test", "TEST_ACTION", "test_resource", region="South")
    intact_after, _ = verify_audit_chain(test_db)
    assert intact_after is True

def test_executive_overview_metrics(test_db):
    admin = test_db.query(User).filter(User.role == "super_admin").first()
    overview = get_executive_overview(test_db, admin)
    assert overview["total_leads"] > 0
    assert overview["total_customers"] > 0
    assert overview["active_projects"] >= 5
    assert overview["crm_sync_health"] in ("Healthy", "Syncing", "Degraded")

def test_record_explorer_server_side_pagination(test_db):
    admin = test_db.query(User).filter(User.role == "super_admin").first()
    res = query_records_paginated(
        db=test_db,
        module="leads",
        page=1,
        limit=10,
        current_user=admin
    )
    assert res["total"] > 0
    assert len(res["items"]) <= 10
    assert "customer_name" in res["items"][0]

def test_regional_abac_scoping(test_db):
    south_mgr = test_db.query(User).filter(User.email == "south.mgr@demo.local").first()
    res = query_records_paginated(
        db=test_db,
        module="leads",
        page=1,
        limit=20,
        current_user=south_mgr
    )
    for lead in res["items"]:
        assert lead["region"] == "South"

def test_workload_optimization_and_assignment_workflow(test_db):
    admin = test_db.query(User).filter(User.role == "super_admin").first()
    leads = test_db.query(Lead).filter(Lead.region == "South").limit(3).all()
    lead_ids = [l.id for l in leads]

    # 1. Preview
    allocations = evaluate_lead_allocations(test_db, lead_ids, admin)
    assert len(allocations) == len(lead_ids)
    for alloc in allocations:
        assert "recommended_assignee_name" in alloc
        assert "reason" in alloc

    batch_id = AssignmentService.create_preview_job(test_db, allocations, admin)
    assert batch_id.startswith("BATCH-")

    # 2. Execution with Manager Approval
    exec_result = AssignmentService.execute_assignment_batch(
        db=test_db,
        batch_id=batch_id,
        idempotency_key=f"IDEMP-{batch_id}",
        approved=True,
        manager=admin
    )
    assert exec_result["status"] == "completed"
    assert exec_result["success_count"] == len(lead_ids)

    # 3. Idempotency test (calling again returns already_completed)
    idemp_result = AssignmentService.execute_assignment_batch(
        db=test_db,
        batch_id=batch_id,
        idempotency_key=f"IDEMP-{batch_id}",
        approved=True,
        manager=admin
    )
    assert idemp_result["status"] == "already_completed"

def test_ai_agent_orchestrator(test_db):
    admin = test_db.query(User).filter(User.role == "super_admin").first()
    
    # Query intent
    res_query = MasterOrchestrator.process_request(test_db, admin, "Show all leads in South region")
    assert res_query["intent"] == "query"
    assert "South" in res_query["message"] or len(res_query["evidence"]) > 0

    # Analysis intent
    res_analysis = MasterOrchestrator.process_request(test_db, admin, "Which project has the highest conversion rate?")
    assert res_analysis["intent"] == "analysis"
    assert len(res_analysis["evidence"]) > 0

    # Action intent
    res_action = MasterOrchestrator.process_request(test_db, admin, "Recommend executives for unassigned leads")
    assert res_action["intent"] == "action"
    assert "Workload Optimization" in res_action["agent_name"]
