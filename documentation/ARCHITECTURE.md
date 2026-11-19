# System Architecture — Centralized Real Estate Intelligence & Operations Command Center

## 1. System Overview & Executive Summary

The Centralized Real Estate Intelligence & Operations Command Center serves as the unified operational interface connecting the organization's central database, existing CRM, employee access management, live operational monitoring, and productivity analytics.

The platform is designed to consolidate **800,000+ customer and lead records** from disparate Excel files, legacy CRM systems, and departmental repositories into a single, high-performance, tamper-evident PostgreSQL database while enforcing strict privacy, security, and access controls.

The operational paradigm follows:
> **Observe ➔ Analyze ➔ Decide ➔ Execute ➔ Monitor**

---

## 2. Six Logical Architectural Layers

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. User & Application Layer                                            │
│    Management · Super Admin · Regional Managers · Sales Executives     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTPS (TLS 1.3)
┌───────────────────────────────────▼────────────────────────────────────┐
│ 2. API Gateway & Security Layer                                        │
│    FastAPI · PBKDF2 Auth · TOTP MFA · JWT · Rate Limiting · ABAC/RBAC  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         ▼                          ▼                          ▼
┌───────────────────┐    ┌─────────────────────┐    ┌────────────────────┐
│ 3. Multi-Agent    │    │ 4. Deterministic    │    │ 5. Integration     │
│    Intelligence   │    │    Business Logic   │    │    & Sync Engine   │
│    Orchestrator   │    │    - Workload Bal.  │    │    - Outbox Queue  │
│    8 Agents       │    │    - Analytics      │    │    - Webhooks      │
│    (LangGraph/LLM)│    │    - Ingestion/Dedup│    │    - CRM Adapter   │
└────────┬──────────┘    └──────────┬──────────┘    └─────────┬──────────┘
         │                          │                         │
         └──────────────────────────┼─────────────────────────┘
                                    │ SQLAlchemy 2.0 (RLS Scoped)
┌───────────────────────────────────▼────────────────────────────────────┐
│ 6. Data Layer (Centralized PostgreSQL)                                 │
│    - Schemas: identity, crm, operations, audit, ingestion, analytics   │
│    - Field-Level Encryption: AES-256-GCM (Phone & Email)               │
│    - Deterministic Duplicate Matching: HMAC-SHA-256                    │
│    - Row-Level Security: SET LOCAL app.region, app.role, app.user_id   │
│    - Cryptographic Audit: Tamper-Evident SHA-256 Hash Chain            │
│    - DPDP Act (2023) Consent Register                                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Functional Modules

### Module A — Centralized Structured Database
- **High-Throughput Ingestion**: Supports streaming CSV and bulk PostgreSQL COPY for 800,000+ leads without memory exhaustion.
- **Field-Level Encryption**: AES-256-GCM authenticated encryption with 12-byte random IVs and 16-byte authentication tags. Keys are versioned (`v1:...`) and stored outside the database.
- **HMAC Deterministic Lookup**: HMAC-SHA-256 generated using a dedicated secret key separate from the encryption key. Enables exact duplicate matching without storing raw PII.
- **Deduplication Engine**: Retains duplicate candidates in `duplicate_candidates` table for human-in-the-loop review. **Never silently deletes records** sharing contact numbers (supporting multi-enquiry and shared family numbers).
- **DPDP Act (2023) Compliance**: `consent_records` captures purpose, notice version (`DPDP-2023-V1`), provenance, and timestamps.

### Module B — CRM Integration & Bidirectional Synchronization
- **Authoritative System Matrix**:
  | Data Entity | Authoritative System of Record |
  | :--- | :--- |
  | Customer Master Profile | Central Database / IAM |
  | Lead Regional Allocation | Central Command Center |
  | Lead Follow-up Status | External CRM |
  | Task Creation & Assignment | Central Command Center |
  | Communication Logs | External CRM (Synced) |
  | Reporting & Analytics Metrics | Central Semantic Layer |
- **Transactional Outbox**: Events staged atomically in database transaction; dispatched asynchronously by Celery workers to prevent data loss.
- **Idempotency Keys**: Cryptographic event hashes prevent duplicate processing from CRM webhooks.

### Module C — IAM & Enterprise Access Control
- **User Hierarchy**:
  - `super_admin`: Full configuration, unmasked PII access, audit verification.
  - `admin`: Technical administration and user provisioning.
  - `management`: Enterprise-wide dashboards, workload rebalancing, and bulk approvals.
  - `regional_manager`: Regional data boundaries (South, North, West, East).
  - `dept_manager`: Departmental team performance monitoring.
  - `employee`: Assigned leads, tasks, and follow-ups only.
  - `auditor`: Read-only access to tamper-evident audit logs and compliance registers.
- **ABAC + RLS**: Multi-attribute enforcement combining User Role, Department, and Region.

### Module D — Tamper-Evident Audit & Activity Engine
- **Application Activity Stream**: Live feed of business activities (SSE broadcaster) with correlation IDs.
- **Cryptographic Audit Chain**: SHA-256 previous-hash chaining `hash = SHA256(prev_hash + user + action + resource + ts)`.
- **Database Immutability**: `REVOKE UPDATE, DELETE, TRUNCATE` on `audit_log`, `access_logs`, and `consent_records`.

### Module E — Management Dashboard Suite
1. **Executive Overview**: High-level KPIs (Total Leads, Active Projects, Pipeline Valuation ₹Cr, Overdue Tasks, CRM Sync Health).
2. **Record Explorer**: Server-side paginated, multi-column filtered explorer across Customers, Leads, Projects, Units, and Tasks with role-aware masking.
3. **CRM Operations Center**: Individual and bulk lead assignment with explainable allocation recommendations.
4. **Sales Intelligence**: Funnel breakdown, marketing channels, and project-wise conversion rates.
5. **Productivity Dashboard**: Task completion rate (%), lead response time (hrs), follow-up compliance (%), resolution time (days), and composite productivity scores.
6. **Distribution & Automated Workload Balancer**: Geographic distribution, channel breakdown, unassigned lead queue, overload flags, and automated 1-click rebalancing recommendations.
7. **Bulk Ingestion & Deduplication Center**: File upload landing zone, SHA-256 checksums, duplicate review drawer, and 800k scale benchmark.
8. **IAM & Security Governance**: Registered users, MFA adoption rate, failed logins (7d), and locked accounts.
9. **Accessibility Intelligence**: 24-hour access heatmaps, cross-region boundary breach alerts, and off-hour access detection.
10. **Live Activity Stream**: Real-time SSE updates for every platform event.

---

## 4. Multi-Agent AI Framework

| Agent | Responsibility | Example Prompt |
| :--- | :--- | :--- |
| **Master Orchestrator** | Intent classification, ABAC perimeter enforcement, dispatching | Coordinates all incoming requests |
| **Data Query Agent** | Natural language to authorized SQLAlchemy queries | "Show all active leads from South region" |
| **Business Insight Agent** | Conversion bottlenecks & project performance | "Which project has the highest conversion rate?" |
| **CRM Operations Agent** | Task generation & lead status progression | "Assign 15 unassigned leads to available executives" |
| **Workload Optimization Agent** | Capacity, specialization & allocation heuristics | "Recommend executives for new South leads" |
| **Monitoring Agent** | Operational health & CRM sync telemetry | "Show latest CRM sync failures" |
| **Reporting Agent** | Formatted summaries and executive digests | "Generate monthly productivity summary" |
| **Risk & Anomaly Agent** | Cross-region access, abnormal distribution & duplicates | "Detect unusual lead reassignment patterns" |

---

## 5. Security & Disaster Recovery Metrics

- **Target RPO (Recovery Point Objective)**: 15 minutes (Continuous WAL archiving).
- **Target RTO (Recovery Time Objective)**: 4 hours.
- **Data Protection Standard**: Indian Digital Personal Data Protection Act, 2023 (DPDP Act).
