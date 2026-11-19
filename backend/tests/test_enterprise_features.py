"""Enterprise Security, Ingestion, DPDP Act, and Specialized Dashboards Tests."""
import io
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.core.security import (
    encrypt_aes_gcm, decrypt_aes_gcm, compute_lookup_hmac,
    normalize_indian_mobile, normalize_email
)
from backend.app.models.identity import User, Role, Permission, AccessLog
from backend.app.models.crm import Customer, Lead, ConsentRecord
from backend.app.models.ingestion import ImportBatch, DuplicateCandidate, DuplicateResolution
from backend.app.services.seed_service import seed_database
from backend.app.services.analytics_service import (
    get_iam_dashboard,
    get_accessibility_dashboard,
    get_productivity_dashboard,
    get_distribution_dashboard
)

@pytest.fixture(scope="module")
def enterprise_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    seed_database(session)
    yield session
    session.close()

def test_aes_gcm_and_hmac_cryptography():
    """Verify AES-256-GCM authenticated encryption and deterministic HMAC-SHA-256."""
    raw_mobile = "+91 98450-12345"
    norm_mobile = normalize_indian_mobile(raw_mobile)
    assert norm_mobile == "9845012345"

    raw_email = "  Client.TEST@Company.COM  "
    norm_email = normalize_email(raw_email)
    assert norm_email == "client.test@company.com"

    # AES-256-GCM encryption & decryption
    encrypted = encrypt_aes_gcm(norm_mobile)
    assert encrypted.startswith("v1:")
    decrypted = decrypt_aes_gcm(encrypted)
    assert decrypted == norm_mobile

    # HMAC deterministic duplicate matching
    hmac1 = compute_lookup_hmac(norm_mobile)
    hmac2 = compute_lookup_hmac("9845012345")
    assert hmac1 == hmac2
    assert len(hmac1) == 64  # SHA-256 hex length

def test_iam_dashboard_analytics(enterprise_db):
    """Test IAM & Identity Governance analytics from Enterprise.txt."""
    admin_user = enterprise_db.scalar(select(User).where(User.role == "super_admin"))
    iam_data = get_iam_dashboard(enterprise_db, admin_user)

    assert iam_data["total_users"] >= 10
    assert iam_data["active_users"] >= 10
    assert len(iam_data["users_by_role"]) >= 4
    assert len(iam_data["users_by_region"]) >= 4
    assert "mfa_enrolled" in iam_data
    assert "failed_logins_7d" in iam_data

def test_accessibility_intelligence_dashboard(enterprise_db):
    """Test period and regional access intelligence and compliance detection."""
    admin_user = enterprise_db.scalar(select(User).where(User.role == "super_admin"))
    access_data = get_accessibility_dashboard(enterprise_db, admin_user)

    assert access_data["total_access_events"] > 0
    assert len(access_data["regional_distribution"]) >= 2
    assert len(access_data["hourly_distribution"]) == 24
    assert "cross_region_attempts" in access_data

def test_productivity_dashboard_kpis(enterprise_db):
    """Test Productivity KPIs: Task completion, response time, follow-up rate, conversion rate."""
    admin_user = enterprise_db.scalar(select(User).where(User.role == "super_admin"))
    prod_data = get_productivity_dashboard(enterprise_db, admin_user)

    assert 0 <= prod_data["task_completion_rate"] <= 100
    assert prod_data["lead_response_time_hours"] > 0
    assert 0 <= prod_data["followup_completion_rate"] <= 100
    assert 0 <= prod_data["conversion_rate"] <= 100
    assert len(prod_data["employee_rankings"]) > 0
    assert len(prod_data["department_benchmarks"]) > 0

def test_distribution_dashboard_and_workload_rebalancing(enterprise_db):
    """Test distribution reports, unassigned lead queues, and automated rebalancing recommendations."""
    admin_user = enterprise_db.scalar(select(User).where(User.role == "super_admin"))
    dist_data = get_distribution_dashboard(enterprise_db, admin_user)

    assert len(dist_data["lead_distribution_by_region"]) >= 3
    assert len(dist_data["customer_distribution_by_source"]) >= 3
    assert len(dist_data["employee_workload_distribution"]) > 0
    # Overload detection should be computed
    assert "overloaded_employees_count" in dist_data
    assert isinstance(dist_data["rebalance_recommendations"], list)

def test_dpdp_act_consent_registers(enterprise_db):
    """Test DPDP Act 2023 customer consent records."""
    consents = enterprise_db.scalars(select(ConsentRecord)).all()
    assert len(consents) > 0
    c0 = consents[0]
    assert c0.consent_given is True
    assert c0.notice_version.startswith("DPDP-2023")

def test_bulk_ingestion_and_deduplication(enterprise_db):
    """Test bulk ingestion batch and human-in-the-loop deduplication resolution."""
    batch = enterprise_db.scalar(select(ImportBatch).order_by(ImportBatch.uploaded_at.desc()))
    assert batch is not None
    assert batch.total_records > 0
    assert len(batch.file_checksum) == 64

    # Verify duplicate candidate exists and can be resolved
    candidate = enterprise_db.scalar(select(DuplicateCandidate).where(DuplicateCandidate.batch_id == batch.id))
    assert candidate is not None
    assert candidate.status == "pending_review"

    # Resolve candidate
    candidate.status = "merged"
    resolution = DuplicateResolution(
        candidate_id=candidate.id,
        resolution_action="merged",
        resolved_by="admin-user-id",
        notes="Customer identified as existing repeat client. Merged enquiry."
    )
    enterprise_db.add(resolution)
    enterprise_db.commit()

    reloaded = enterprise_db.get(DuplicateCandidate, candidate.id)
    assert reloaded.status == "merged"
