"""Users, Roles, and Permissions Management Endpoints (IAM)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import hash_pw, ALL_SCOPE, REGION_SCOPE, PERMS
from backend.app.core.audit import log_audit
from backend.app.models.identity import User, Role, Permission
from backend.app.api.v1.auth import get_current_user

router = APIRouter(tags=["IAM & Access Management"])

class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    role: str
    department: str = "Sales"
    region: str = "South"
    branch: str = "Bengaluru South"
    expertise: str = "Residential"

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    department: str
    region: str
    branch: str
    expertise: str
    active: bool
    active_leads_count: int

@router.get("/users", response_model=List[UserResponse])
def list_users(
    region: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = select(User)
    if current_user.role in REGION_SCOPE:
        q = q.where(User.region == current_user.region)
    elif current_user.role not in ALL_SCOPE:
        q = q.where(User.id == current_user.id)
    
    if region and (current_user.role in ALL_SCOPE or region == current_user.region):
        q = q.where(User.region == region)
    if role:
        q = q.where(User.role == role)

    users = db.scalars(q.order_by(User.name)).all()
    return [
        UserResponse(
            id=u.id,
            email=u.email,
            name=u.name,
            role=u.role,
            department=u.department,
            region=u.region,
            branch=u.branch or "",
            expertise=u.expertise or "",
            active=u.active,
            active_leads_count=u.active_leads_count
        )
        for u in users
    ]

@router.post("/users", response_model=UserResponse)
def create_user(
    req: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ("super_admin", "admin"):
        raise HTTPException(status_code=403, detail="Only Super Admin or Admin can create new user accounts.")

    existing = db.scalar(select(User).where(User.email == req.email.lower().strip()))
    if existing:
        raise HTTPException(status_code=409, detail="A user with this email address already exists.")

    new_user = User(
        email=req.email.lower().strip(),
        name=req.name.strip(),
        pw_hash=hash_pw(req.password),
        role=req.role,
        department=req.department,
        region=req.region,
        branch=req.branch,
        expertise=req.expertise,
        active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_audit(db, current_user.id, "USER_CREATED", f"email:{new_user.email},role:{new_user.role}", region=current_user.region)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        name=new_user.name,
        role=new_user.role,
        department=new_user.department,
        region=new_user.region,
        branch=new_user.branch,
        expertise=new_user.expertise,
        active=new_user.active,
        active_leads_count=new_user.active_leads_count
    )

@router.get("/roles")
def list_roles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    roles = db.scalars(select(Role).order_by(Role.name)).all()
    if not roles:
        # Fallback to predefined roles if none in table
        return [
            {"name": "super_admin", "description": "Full system configuration"},
            {"name": "admin", "description": "Technical administration"},
            {"name": "management", "description": "Organization-wide reports"},
            {"name": "regional_manager", "description": "Assigned regional data"},
            {"name": "dept_manager", "description": "Department-level data"},
            {"name": "employee", "description": "Assigned records and tasks"},
            {"name": "auditor", "description": "Read-only audit access"}
        ]
    return [{"id": r.id, "name": r.name, "description": r.description} for r in roles]

@router.get("/permissions")
def list_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    perms = db.scalars(select(Permission).order_by(Permission.module, Permission.code)).all()
    if not perms:
        return [
            {"code": "audit:read", "module": "audit", "description": "Read-only audit inspection"},
            {"code": "export", "module": "reports", "description": "Export datasets"},
            {"code": "customer:write", "module": "crm", "description": "Manage customers"},
            {"code": "lead:assign", "module": "operations", "description": "Lead allocation"}
        ]
    return [{"id": p.id, "code": p.code, "module": p.module, "description": p.description} for p in perms]
