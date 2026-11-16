"""Reports and Export Endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import PERMS
from backend.app.models.identity import User
from backend.app.api.v1.auth import get_current_user
from backend.app.services.report_service import generate_leads_report_csv

router = APIRouter(prefix="/reports", tags=["Reporting & Export"])

@router.get("/export/leads.csv")
def export_leads_csv(
    region: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in PERMS["export"]:
        raise HTTPException(status_code=403, detail="Not authorized to export data.")

    csv_data = generate_leads_report_csv(db, current_user, region)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_report.csv"}
    )
