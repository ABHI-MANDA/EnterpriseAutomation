"""Enterprise Security, Ingestion, DPDP Act, and Specialized Dashboards Tests."""
import io
import json
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from backend.app.core.database import Base
from backend.app.core.security import (
    encrypt_aes_gcm, decrypt_aes_gcm, compute_lookup_hmac,
    normalize_indian_mobile, normalize_email
)
from backend.app.models.identity import User, Role, Permission, AccessLog
from backend.app.models.organization import City, Zone, Locality
from backend.app.models.real_estate import Project, PropertyType
from backend.app.models.crm import Customer, Lead, ConsentRecord, LeadAllocation
from backend.app.models.ingestion import ImportBatch, DuplicateCandidate, DuplicateResolution, UnmatchedEntity
from backend.app.services.seed_service import seed_database
from backend.app.services.cleaning_engine import CleaningEngine
from backend.app.services.record_service import query_records_paginated
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

def test_cleaning_engine_standardization():
    """Test CleaningEngine normalizes aliases, phones, emails, and swaps inverted budgets."""
    raw_lead = {
        "name": "  Vikramaditya Rao  ",
        "mobile": "+91 (98450) 88899",
        "email": "  VIKRAM.RAO@outlook.COM ",
        "city": "Bangalore",
        "locality": "White Field",
        "property_type": "2bhk",
        "min_price": "15000000",
        "max_price": "8000000",
        "project": "Godrej Splendour"
    }

    clean = CleaningEngine.clean_record(raw_lead)

    assert clean["name"] == "Vikramaditya Rao"
    assert clean["mobile"] == "9845088899"
    assert clean["is_valid_phone"] is True
    assert clean["email"] == "vikram.rao@outlook.com"
    assert clean["is_valid_email"] is True
    assert clean["city"] == "Bengaluru"
    assert clean["locality"] == "Whitefield"
    assert clean["property_type"] == "Apartment - 2 BHK"
    # min_price and max_price swapped because 15,000,000 > 8,000,000
    assert clean["min_price"] == 8000000.0
    assert clean["max_price"] == 15000000.0

def test_lead_warehouse_schema_and_querying(enterprise_db):
    """Test querying warehouse leads with relational geographic and property attributes."""
    admin_user = enterprise_db.scalar(select(User).where(User.role == "super_admin"))

    # Query leads with price range filters
    res = query_records_paginated(
        db=enterprise_db,
        module="leads",
        page=1,
        limit=10,
        filters={"min_price": 5000000, "max_price": 25000000},
        current_user=admin_user
    )

    assert res["total"] > 0
    first_item = res["items"][0]
    assert "city_name" in first_item
    assert "locality_name" in first_item
    assert "property_type_name" in first_item
    assert "allocated_to_name" in first_item
    assert "has_encrypted_pii" in first_item

def test_lead_allocation_lifecycle(enterprise_db):
    """Test lead allocation logging and multi-module query."""
    lead = enterprise_db.scalar(select(Lead))
    user = enterprise_db.scalar(select(User).where(User.role == "employee"))
    admin = enterprise_db.scalar(select(User).where(User.role == "super_admin"))

    assert user is not None
    alloc = LeadAllocation(
        lead_id=lead.id,
        employee_id=user.id,
        previous_employee_id=lead.allocated_to,
        allocated_by=admin.id,
        allocation_status="active",
        notes="Automated round-robin assignment based on locality match"
    )
    enterprise_db.add(alloc)
    enterprise_db.commit()

    alloc_res = query_records_paginated(
        db=enterprise_db,
        module="lead_allocations",
        page=1,
        limit=10,
        filters={"lead_id": lead.id},
        current_user=admin
    )
    assert alloc_res["total"] >= 1
    assert alloc_res["items"][0]["employee_id"] == user.id

def test_import_batch_quality_report_and_unmatched_entities(enterprise_db):
    """Test import batch quality counters and unmatched entities inspection."""
    batch = enterprise_db.scalar(select(ImportBatch).order_by(ImportBatch.uploaded_at.desc()))
    assert batch is not None
    assert batch.valid_records >= 0
    assert batch.missing_mobile >= 0
    assert batch.invalid_emails >= 0
    
    # Check JSON quality report
    report = json.loads(batch.quality_report_json)
    assert "total_imported_records" in report or "total_records" in report
    assert "valid_records" in report
    assert "duplicate_candidates" in report

    # Test querying unmatched_entities
    admin = enterprise_db.scalar(select(User).where(User.role == "super_admin"))
    unmatched_res = query_records_paginated(
        db=enterprise_db,
        module="unmatched_entities",
        page=1,
        limit=10,
        current_user=admin
    )
    assert "items" in unmatched_res
    assert unmatched_res["total"] >= 1
