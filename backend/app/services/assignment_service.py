"""Bulk Assignment Service with Idempotency, Per-Record Tracking, and Approval Workflow."""
import uuid
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.security import now_utc, PERMS
from backend.app.core.events import publish_event
from backend.app.core.audit import log_audit
from backend.app.models.identity import User
from backend.app.models.crm import Lead
from backend.app.models.operations import AssignmentJob, AssignmentRecord
from backend.app.services.crm_adapter import CRMAdapter

class AssignmentService:
    @staticmethod
    def create_preview_job(
        db: Session,
        allocations: List[Dict[str, Any]],
        creator: User
    ) -> str:
        batch_id = "BATCH-" + uuid.uuid4().hex[:8].upper()
        idempotency_key = f"IDEMP-{batch_id}"

        job = AssignmentJob(
            batch_id=batch_id,
            idempotency_key=idempotency_key,
            created_by=creator.id,
            status="preview",
            total_leads=len(allocations),
            success_count=0,
            fail_count=0
        )
        db.add(job)
        db.flush()

        for alloc in allocations:
            record = AssignmentRecord(
                job_id=job.id,
                lead_id=alloc["lead_id"],
                recommended_assignee_id=alloc["recommended_assignee_id"],
                final_assignee_id=alloc["recommended_assignee_id"],
                reason=alloc["reason"],
                status="pending",
                crm_sync_status="pending"
            )
            db.add(record)

        db.commit()
        return batch_id

    @staticmethod
    def execute_assignment_batch(
        db: Session,
        batch_id: str,
        idempotency_key: str,
        approved: bool,
        manager: User,
        custom_allocations: List[Dict[str, Any]] | None = None
    ) -> Dict[str, Any]:
        # Permission check
        if manager.role not in PERMS["lead:assign"]:
            return {
                "batch_id": batch_id,
                "status": "unauthorized",
                "total_leads": 0,
                "success_count": 0,
                "fail_count": 0,
                "records": []
            }

        job = db.scalar(select(AssignmentJob).where(AssignmentJob.batch_id == batch_id))
        if not job:
            return {"batch_id": batch_id, "status": "job_not_found", "total_leads": 0, "success_count": 0, "fail_count": 0, "records": []}

        # Idempotency check: if already completed, return existing results
        if job.status == "completed":
            records = db.scalars(select(AssignmentRecord).where(AssignmentRecord.job_id == job.id)).all()
            return {
                "batch_id": batch_id,
                "status": "already_completed",
                "total_leads": job.total_leads,
                "success_count": job.success_count,
                "fail_count": job.fail_count,
                "records": [
                    {
                        "lead_id": r.lead_id,
                        "assignee_id": r.final_assignee_id,
                        "status": r.status,
                        "crm_sync_status": r.crm_sync_status,
                        "error": r.error_message
                    } for r in records
                ]
            }

        if not approved:
            job.status = "rejected"
            db.commit()
            log_audit(db, manager.id, "LEAD_BATCH_REJECTED", f"batch:{batch_id}", region=manager.region)
            return {"batch_id": batch_id, "status": "rejected", "total_leads": job.total_leads, "success_count": 0, "fail_count": 0, "records": []}

        # Apply any manual overrides from manager
        custom_map = {c["lead_id"]: c["final_assignee_id"] for c in (custom_allocations or []) if "lead_id" in c and "final_assignee_id" in c}

        records = db.scalars(select(AssignmentRecord).where(AssignmentRecord.job_id == job.id)).all()
        success_count = 0
        fail_count = 0
        record_results = []

        for rec in records:
            if rec.lead_id in custom_map:
                rec.final_assignee_id = custom_map[rec.lead_id]

            lead = db.get(Lead, rec.lead_id)
            target_user = db.get(User, rec.final_assignee_id)

            if not lead or not target_user:
                rec.status = "failed"
                rec.crm_sync_status = "failed"
                rec.error_message = "Lead or Assignee not found"
                fail_count += 1
                record_results.append({
                    "lead_id": rec.lead_id,
                    "assignee_id": rec.final_assignee_id,
                    "status": "failed",
                    "crm_sync_status": "failed",
                    "error": rec.error_message
                })
                continue

            # Deterministic CRM execution
            sync_ok, crm_msg = CRMAdapter.sync_lead_assignment(lead.id, target_user.id, target_user.email)
            
            if sync_ok:
                lead.assignee_id = target_user.id
                target_user.active_leads_count += 1
                rec.status = "success"
                rec.crm_sync_status = "synced"
                success_count += 1

                # Publish operational event for activity feed & live SSE
                publish_event(
                    db=db,
                    event_type="lead.assigned",
                    actor={"type": "user", "id": manager.id, "name": manager.name},
                    target={"type": "lead", "id": lead.id},
                    action_desc=f"Lead assigned to {target_user.name} ({rec.reason})",
                    status="completed",
                    crm_sync_status="success",
                    correlation_id=batch_id,
                    payload={"lead_id": lead.id, "assignee_id": target_user.id, "region": lead.region}
                )
            else:
                rec.status = "failed"
                rec.crm_sync_status = "failed"
                rec.error_message = crm_msg
                fail_count += 1

            record_results.append({
                "lead_id": rec.lead_id,
                "assignee_id": rec.final_assignee_id,
                "status": rec.status,
                "crm_sync_status": rec.crm_sync_status,
                "error": rec.error_message
            })

        job.status = "completed" if fail_count == 0 else ("partial_failure" if success_count > 0 else "failed")
        job.success_count = success_count
        job.fail_count = fail_count
        job.executed_at = now_utc()
        db.commit()

        log_audit(db, manager.id, "LEAD_BATCH_EXECUTED", f"batch:{batch_id}|success:{success_count}|failed:{fail_count}", region=manager.region)

        return {
            "batch_id": batch_id,
            "status": job.status,
            "total_leads": len(records),
            "success_count": success_count,
            "fail_count": fail_count,
            "records": record_results
        }
