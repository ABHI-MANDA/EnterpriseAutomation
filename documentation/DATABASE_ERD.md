# Database ERD and Logical Schema Specification

## 1. Logical Schemas

### A. identity
- `users`: User identity, authentication credentials (PBKDF2 hash), role (`super_admin`, `admin`, `management`, `regional_manager`, `dept_manager`, `employee`, `auditor`), region, department, branch, MFA secret, status, fail counters, lockout timestamp.
- `roles`: Role definitions and capability masks.
- `user_sessions`: Active session records, token expirations, device metadata.

### B. organization
- `regions`: Regional jurisdictions (e.g. `North`, `South`, `East`, `West`).
- `branches`: Physical business branches mapped to regions.
- `departments`: Functional departments (`Sales`, `Customer Support`, `Operations`, `Finance`).
- `employees`: Employee operational profiles, active status, expertise tags, current assigned lead quotas.

### C. real_estate
- `projects`: Real estate developments (name, code, region, branch, status, total units, launch date).
- `properties`: Specific buildings, phases, or blocks within a project.
- `units`: Individual units (unit number, type, BHK, carpet area, price, status: `available`, `reserved`, `sold`, `blocked`).
- `viewings`: Scheduled property visits and customer feedback.

### D. crm
- `customers`: Customer profiles (name, email, phone, masked versions, region, source, assignee_id, version).
- `leads`: Lead records (customer_id, project_id, region, branch, status: `new`, `contacted`, `qualified`, `negotiation`, `won`, `lost`, priority: `urgent`, `high`, `normal`, `low`, source, assignee_id, first_response_at, crm_external_id).
- `deals`: Commercial transactions (lead_id, unit_id, deal_value, status, expected_close_date, closed_at).
- `tasks`: Operational action items (title, description, lead_id, assignee_id, due_date, done_at, priority, status).
- `followups`: Customer interactions (lead_id, employee_id, notes, outcome, scheduled_at, completed_at).

### E. operations
- `assignment_jobs`: Bulk lead assignment batches (batch_id, idempotency_key, created_by, status: `draft`, `preview`, `approved`, `executing`, `completed`, `failed`, total_leads, success_count, fail_count).
- `assignment_records`: Individual lead assignment items within a batch (job_id, lead_id, recommended_assignee_id, final_assignee_id, reason, crm_sync_status, error_message).
- `operational_events`: System business events published for activity feeds.

### F. integration
- `crm_outbox`: Transactional outbox table for outgoing synchronization events (event, payload, status: `pending`, `sent`, `failed`, retry_count, last_attempt, error_details).
- `crm_inbox`: Processed inbound webhook events ensuring idempotency.
- `conflict_log`: Detected data conflicts between central database and external CRM.

### G. audit
- `audit_logs`: Append-only, tamper-evident hash-chained logs (id, ts, user_id, region, action, resource, result, ip_hash, prev_hash, hash).

### H. dashboards
- `dashboards`: Custom dashboards (id, title, owner_id, is_default, role_target, layout_json).
- `dashboard_widgets`: Reusable widget definitions (id, dashboard_id, widget_type, metric_key, config_json, position_json).
- `saved_views`: User-saved filter criteria and column configurations.

### I. agents
- `agent_executions`: History of multi-agent runs (id, user_id, agent_name, request_text, intent, status, result_summary, execution_time_ms).
- `agent_tool_calls`: Log of deterministic tools invoked during agent processing.
- `agent_proposals`: Stored recommendation plans requiring human authorization before execution.
