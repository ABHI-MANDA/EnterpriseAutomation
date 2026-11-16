"""Realistic Synthetic Data Seeder for Real Estate Enterprise Platform.
Does not contain any real customer PII.
"""
import os
import random
import secrets
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from backend.app.core.security import hash_pw, now_utc
from backend.app.core.audit import log_audit
from backend.app.models.identity import User
from backend.app.models.organization import Region, Branch, Department
from backend.app.models.real_estate import Project, Property, Unit
from backend.app.models.crm import Customer, Lead, Deal, Task, FollowUp
from backend.app.models.dashboards import Dashboard
from backend.app.services.dashboard_service import get_default_layout_for_role
import json

def seed_database(db: Session):
    # Check if already seeded
    if db.scalar(select(func.count(User.id))):
        return

    print("--- Initializing Real Estate Enterprise Database Seed ---")
    pw = os.environ.get("SEED_PASSWORD", "AdminPass@2026")
    ph = hash_pw(pw)

    # 1. Regions & Branches
    regions_data = [
        ("South", "S", "Bengaluru South"),
        ("North", "N", "Delhi NCR"),
        ("West", "W", "Mumbai West"),
        ("East", "E", "Kolkata Central")
    ]
    for rname, rcode, bname in regions_data:
        r = Region(name=rname, code=rcode)
        db.add(r)
        db.flush()
        db.add(Branch(name=bname, region_id=r.id, code=f"BR-{rcode}01"))
    
    # 2. Users & Staff
    staff = [
        User(email="admin@demo.local", name="Asha Admin", role="super_admin", region="South", branch="Bengaluru South", pw_hash=ph, department="Executive"),
        User(email="mgmt@demo.local", name="Meera Management", role="management", region="South", branch="Bengaluru South", pw_hash=ph, department="Executive"),
        User(email="auditor@demo.local", name="Arun Auditor", role="auditor", region="South", branch="Bengaluru South", pw_hash=ph, department="Audit"),
        User(email="south.mgr@demo.local", name="Sanjay South", role="regional_manager", region="South", branch="Bengaluru South", pw_hash=ph, department="Sales"),
        User(email="north.mgr@demo.local", name="Nisha North", role="regional_manager", region="North", branch="Delhi NCR", pw_hash=ph, department="Sales"),
    ]
    db.add_all(staff)
    db.flush()

    sales_execs = [
        User(email="arjun.south@demo.local", name="Arjun Rao", role="employee", region="South", branch="Bengaluru South", pw_hash=ph, department="Sales", expertise="Luxury, Villas", active_leads_count=12),
        User(email="priya.south@demo.local", name="Priya Sharma", role="employee", region="South", branch="Bengaluru South", pw_hash=ph, department="Sales", expertise="Residential, High-Rise", active_leads_count=8),
        User(email="rahul.north@demo.local", name="Rahul Verma", role="employee", region="North", branch="Delhi NCR", pw_hash=ph, department="Sales", expertise="Commercial, Plots", active_leads_count=15),
        User(email="ananya.north@demo.local", name="Ananya Gupta", role="employee", region="North", branch="Delhi NCR", pw_hash=ph, department="Sales", expertise="Luxury, Penthouses", active_leads_count=6),
        User(email="vikram.west@demo.local", name="Vikram Mehta", role="employee", region="West", branch="Mumbai West", pw_hash=ph, department="Sales", expertise="Sea-facing, Premium", active_leads_count=18),
        User(email="sneha.east@demo.local", name="Sneha Roy", role="employee", region="East", branch="Kolkata Central", pw_hash=ph, department="Sales", expertise="Affordable, Family", active_leads_count=10)
    ]
    db.add_all(sales_execs)
    db.flush()

    # 3. Projects, Properties & Units
    projects_data = [
        ("Prestige Green Valley", "PGV-01", "South", "Bengaluru South", "Residential", 120),
        ("Sobha Waterfront Luxury", "SWL-02", "South", "Bengaluru South", "Luxury", 80),
        ("DLF Imperial Park", "DIP-03", "North", "Delhi NCR", "Residential", 150),
        ("Lodha Solitaire Tower", "LST-04", "West", "Mumbai West", "Luxury", 90),
        ("Godrej Horizon Enclave", "GHE-05", "East", "Kolkata Central", "Mixed", 110)
    ]
    created_projects = []
    created_units = []

    for name, code, reg, br, ptype, total_u in projects_data:
        proj = Project(name=name, code=code, region=reg, branch=br, project_type=ptype, status="Active", total_units=total_u)
        db.add(proj)
        db.flush()
        created_projects.append(proj)

        prop = Property(project_id=proj.id, name=f"{name} Tower A", total_floors=24, region=reg)
        db.add(prop)
        db.flush()

        # Create units
        for u_idx in range(1, 16):
            bhk = "4 BHK" if "Luxury" in ptype else ("3 BHK" if u_idx % 2 == 0 else "2 BHK")
            price = 28000000.0 if "Luxury" in ptype else (16000000.0 if bhk == "3 BHK" else 9500000.0)
            status = "sold" if u_idx <= 4 else ("reserved" if u_idx <= 6 else "available")
            unit = Unit(
                project_id=proj.id,
                property_id=prop.id,
                unit_number=f"T1-{u_idx:03d}",
                bhk=bhk,
                area_sqft=1400.0 if bhk == "3 BHK" else (2200.0 if bhk == "4 BHK" else 1050.0),
                price=price,
                status=status,
                region=reg
            )
            db.add(unit)
            created_units.append(unit)

    db.flush()

    # 4. Customers & Leads
    lead_sources = ["Website", "Referral", "Property Portal", "Walk-in", "Digital Ads"]
    lead_stages = ["new", "contacted", "qualified", "negotiation", "won", "lost"]
    priorities = ["normal", "normal", "high", "urgent", "low"]

    all_users = sales_execs
    regions = ["South", "North", "West", "East"]

    created_leads = []
    for i in range(1, 121):
        reg = regions[i % 4]
        source = lead_sources[i % len(lead_sources)]
        status = lead_stages[i % len(lead_stages)]
        prio = priorities[i % len(priorities)]
        
        # Pick regional employee
        reg_execs = [e for e in all_users if e.region == reg]
        assigned_user = reg_execs[i % len(reg_execs)] if reg_execs and (i % 7 != 0) else None

        cust = Customer(
            name=f"Prospective Client {i}",
            email=f"client{i:03d}@enterprise-realestate.demo",
            phone=f"+91 98450 {i:05d}",
            region=reg,
            branch=f"{reg} Hub",
            source=source,
            assignee_id=assigned_user.id if assigned_user else None
        )
        db.add(cust)
        db.flush()

        proj = next((p for p in created_projects if p.region == reg), created_projects[0])
        lead = Lead(
            customer_id=cust.id,
            project_id=proj.id,
            region=reg,
            branch=proj.branch,
            status=status,
            priority=prio,
            source=source,
            budget=random.choice([12000000.0, 18000000.0, 25000000.0, 35000000.0]),
            assignee_id=assigned_user.id if assigned_user else None,
            crm_external_id=f"CRM-LD-{i:05d}",
            created_at=now_utc() - timedelta(days=random.randint(1, 45))
        )
        db.add(lead)
        created_leads.append(lead)

    db.flush()

    # 5. Deals, Tasks & Followups
    for i, lead in enumerate(created_leads[:40]):
        assigned_id = lead.assignee_id or sales_execs[0].id
        # Task
        due_date = now_utc() + timedelta(days=random.randint(-5, 10))
        done = due_date - timedelta(days=1) if random.random() < 0.6 else None
        db.add(Task(
            title=f"Initial Project Presentation for Lead {i+1}",
            description=f"Walkthrough floorplans and financial structuring for {lead.region} property.",
            lead_id=lead.id,
            assignee_id=assigned_id,
            region=lead.region,
            priority=lead.priority,
            due=due_date,
            done_at=done
        ))

        # Followup
        db.add(FollowUp(
            lead_id=lead.id,
            employee_id=assigned_id,
            region=lead.region,
            notes="Discussed 3 BHK pricing and possession timeline.",
            outcome=random.choice(["completed", "positive", "rescheduled"]),
            scheduled_at=now_utc() - timedelta(days=random.randint(1, 10)),
            completed_at=now_utc() - timedelta(hours=random.randint(2, 48))
        ))

        # Deal for won leads
        if lead.status == "won":
            db.add(Deal(
                lead_id=lead.id,
                deal_value=lead.budget,
                status="closed_won",
                region=lead.region,
                closed_at=now_utc() - timedelta(days=random.randint(1, 15))
            ))

    # 6. Default Dashboards for Admin & Management
    for u in staff[:2]:
        layout = get_default_layout_for_role(u.role)
        db.add(Dashboard(
            title="Real Estate Enterprise Command Center",
            owner_id=u.id,
            is_default=True,
            role_target=u.role,
            layout_json=json.dumps(layout)
        ))

    db.commit()

    # Initial Audit Entry
    log_audit(db, staff[0].id, "SYSTEM_INIT_SEED", "Database successfully initialized with synthetic enterprise data.", region="South")
    print(f"\n=======================================================")
    print(f" DEMO ACCOUNTS SEEDED (Password: {pw})")
    print(f" - Super Admin : admin@demo.local")
    print(f" - Management  : mgmt@demo.local")
    print(f" - South Mgr   : south.mgr@demo.local")
    print(f" - North Mgr   : north.mgr@demo.local")
    print(f" - Auditor     : auditor@demo.local")
    print(f"=======================================================\n")
