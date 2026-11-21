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
- `cities` ★: City master table for 800k lead geographic normalization. Fields: id, name, state, country. Canonical values prevent 50,000 Bengaluru records from having 15 spellings.
- `zones` ★: Zone master (South / North / East / West / Central). Links to city and locality.
- `localities` ★: Locality master linked to city_id and zone_id (e.g. Whitefield → Bengaluru → East). Prevents "White Field / Whitfield / Whitifield" inconsistencies.

### C. real_estate
- `property_types` ★: Property type master (Apartment - 2 BHK, Apartment - 3 BHK, Villa, Plot, Penthouse, Commercial Space). Normalizes "2BHK / 2 bhk / flat" into canonical forms.
- `projects`: Real estate developments (name, code, region, branch, status, total units, launch date, **city_id**, **locality_id**, **zone_id**).
- `properties`: Specific buildings, phases, or blocks within a project.
- `units`: Individual units (unit number, type, BHK, carpet area, price, status: `available`, `reserved`, `sold`, `blocked`).
- `viewings`: Scheduled property visits and customer feedback.

### D. crm
- `customers`: Customer profiles (name, email, phone, masked versions, region, source, assignee_id, version).
- `leads` ★ (**Master 800k table**): Full warehouse schema. Fields:
  - Identity: id, customer_id, name
  - Geography: **city_id**, **locality_id**, **zone_id**, region, branch
  - Property: **property_type_id**, project_id
  - Budget: budget (legacy), **min_price**, **max_price**
  - Allocation: assignee_id, **allocated_to**, **allocated_date**
  - Security/PII: **mobile_encrypted** (AES-256-GCM), **email_encrypted**, **mobile_lookup_hash** (keyed HMAC-SHA-256), **email_lookup_hash**
  - CRM: crm_external_id, first_response_at
  - Status: status (new/contacted/qualified/negotiation/won/lost), priority (urgent/high/normal/low), source
- `lead_allocations` ★: Full allocation & reassignment history. Never overwrites current state — every allocation event is a new row. Fields: lead_id, employee_id, previous_employee_id, allocated_by, allocated_date, allocation_status (active/reassigned/completed), notes.
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

### J. ingestion ★
- `import_batches` ★: Tracks every bulk upload (up to 800k+ records). Quality fields:
  - Counters: total_records, valid_records, successful_records, duplicate_candidates, rejected_records
  - Quality: **missing_mobile**, **invalid_emails**, **unmatched_projects_count**, **unmatched_locations_count**
  - Reports: file_checksum (SHA-256), **quality_report_json** (quality_score_percent, counts, breakdown by dimension)
- `duplicate_candidates` ★: Human-in-loop deduplication. Fields: batch_id, existing_customer_id, incoming_name/phone_masked/email_masked, phone_lookup_hmac, email_lookup_hmac, match_reason (exact_mobile_hmac/exact_email_hmac/name_and_phone), confidence_score, status (pending_review/merged/kept_separate/rejected).
- `duplicate_resolutions` ★: Audit record of every deduplication decision (candidate_id, resolution_action, resolved_by, notes, resolved_at).
- `unmatched_entities` ★: Staging for unrecognized city, locality, project, property_type names. Fields: batch_id, entity_type, raw_value, suggested_match, context_info (JSON with occurrence count), resolution_status (pending/mapped/ignored), resolved_to_id.

---

## 2. Key Foreign-Key Relationships

```
leads.customer_id        → customers.id
leads.project_id         → projects.id
leads.property_type_id   → property_types.id  ★
leads.city_id            → cities.id           ★
leads.locality_id        → localities.id       ★
leads.zone_id            → zones.id            ★
leads.assignee_id        → users.id
leads.allocated_to       → users.id            ★

lead_allocations.lead_id      → leads.id       ★
lead_allocations.employee_id  → users.id       ★

localities.city_id  → cities.id                ★
localities.zone_id  → zones.id                 ★
projects.city_id    → cities.id                ★
projects.locality_id → localities.id           ★
projects.zone_id    → zones.id                 ★

duplicate_candidates.batch_id      → import_batches.id
duplicate_resolutions.candidate_id → duplicate_candidates.id
unmatched_entities.batch_id        → import_batches.id  ★
```

---

## 3. Security & Privacy Architecture

| Layer | Implementation |
|---|---|
| Field-level encryption | AES-256-GCM (mobile + email) — `mobile_encrypted`, `email_encrypted` |
| Dedup without plaintext | Keyed HMAC-SHA-256 — `mobile_lookup_hash`, `email_lookup_hash` |
| Row-Level Security | PostgreSQL RLS policies in `database/policies/rls.sql` |
| Access control | RBAC with 7 roles: super_admin → auditor |
| Audit trail | Append-only SHA-256 hash-chained `audit_logs` |
| DPDP Act 2023 | Consent records in `consent_records` with notice_version and purpose fields |
| Data masking | `mask_text()` applied server-side before JSON response |
| Key management | Separate `FIELD_ENCRYPTION_KEY` and `HMAC_LOOKUP_KEY` env vars |

---

## 4. Indexing Strategy (PostgreSQL Production)

| Field | Index Type | Reason |
|---|---|---|
| leads.mobile_lookup_hash | UNIQUE where not null | Dedup lookup |
| leads.email_lookup_hash | B-tree | Dedup lookup |
| leads.city_id | B-tree | City filter (800k records) |
| leads.locality_id | B-tree | Locality filter |
| leads.zone_id | B-tree | Zone filter |
| leads.property_type_id | B-tree | Property type filter |
| leads.min_price, max_price | B-tree | Budget range queries |
| leads.allocated_to | B-tree | Per-employee queries |
| leads.allocated_date | B-tree | Date range allocation reports |
| leads.status, priority | B-tree | Pipeline stage filters |
| lead_allocations.lead_id | B-tree | Allocation history lookups |
| unmatched_entities.batch_id | B-tree | Per-batch admin review |

> **Note**: Avoid indexes on every column. Too many indexes slow bulk imports (PostgreSQL COPY). Add indexes based on actual query patterns. For 800k records, partial indexes (e.g. `WHERE status = 'new'`) can dramatically reduce index size.

---

## 5. Data Cleaning Engine — Alias Dictionaries

The `CleaningEngine` (`backend/app/services/cleaning_engine.py`) handles:

| Input | Standardized Output |
|---|---|
| Bangalore / Banglore / B'lore | **Bengaluru** |
| White Field / whitefield | **Whitefield** |
| 2BHK / 2bhk / 2 BHK / flat | **Apartment - 2 BHK** |
| +91 (98450) 88899 | **9845088899** (10-digit normalized) |
| VIKRAM@GMAIL.COM | **vikram@gmail.com** |
| min_price=15L, max_price=8L | **swapped** → min=8L, max=15L |

Output keys: `name`, `mobile` / `phone`, `is_valid_phone`, `email`, `is_valid_email`, `city`, `locality`, `property_type`, `min_price`, `max_price`, `is_valid`, `project_name`, `allocated_to`.

---

## 6. Data Quality Report Structure

Every `import_batches.quality_report_json` contains:
```json
{
  "quality_score_percent": 98.6,
  "total_records": 850,
  "valid_records": 838,
  "duplicate_candidates": 12,
  "missing_mobile": 0,
  "invalid_emails": 0,
  "counts": { "total": 850, "valid": 838, "duplicates": 12, ... },
  "breakdown": {
    "city_normalization": { "matched": 848, "unmatched": 2, "pct": 99.8 },
    "mobile_validation": { "valid": 850, "invalid": 0, "pct": 100.0 },
    "email_validation": { ... },
    "property_type_match": { ... },
    "budget_range_valid": { "valid": 838, "inverted_swapped": 12, "pct": 100.0 },
    "allocation_assigned": { "assigned": 820, "unassigned": 30, "pct": 96.5 }
  }
}
```

★ = Added/upgraded in this release for the 800k data warehouse architecture.
