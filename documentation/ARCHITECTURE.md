# System Architecture — Centralized Real Estate Intelligence & Operations Command Center

## 1. Overview
The Centralized Real Estate Intelligence & Operations Command Center provides a single glasspane for observing, analyzing, deciding, executing, and monitoring enterprise real estate operations across regions, branches, projects, and sales teams.

The architecture strictly adheres to the principle:
> **Observe -> Analyze -> Decide -> Execute -> Monitor**

It combines:
- **FastAPI Modular Backend** with Python 3.11+
- **Next.js & TypeScript Command Center UI**
- **Central PostgreSQL** partitioned into logical schemas with Row Level Security (RLS)
- **Multi-Agent Orchestration Layer** coordinating 8 specialized agents
- **Deterministic Business Services** for CRM operations and assignment execution
- **Transactional Outbox & Inbox** for bidirectional CRM synchronization
- **Server-Sent Events (SSE)** for near-real-time live activity streaming
- **Tamper-Evident Hash-Chained Audit Logs** for governance and compliance

## 2. Five Operational Layers
1. **Data Layer**: PostgreSQL with logical schemas, database constraints, soft-deletes, and RLS (`SET LOCAL app.region`, `SET LOCAL app.role`, `SET LOCAL app.user_id`).
2. **Intelligence Layer**: Multi-Agent system consisting of Master Orchestrator, Data Query Agent, Business Insight Agent, CRM Operations Agent, Monitoring Agent, Reporting Agent, Risk & Anomaly Agent, and Workload Optimization Agent.
3. **Control Layer**: Universal filter engine, server-side RBAC/ABAC authorization, manager approval gates for batch lead assignments, and idempotency protection.
4. **Visualization Layer**: Reusable widget engine (KPIs, Charts, Timelines, Tables), cross-filtering, and saved dashboard views persisted in PostgreSQL.
5. **Monitoring Layer**: SSE event stream broadcasting all operational activities with correlation IDs, actor details, and CRM synchronization status.

## 3. Communication & Execution Lifecycle
```
User Request / Webhook / Action
       │
       ▼
┌─────────────────────────────────┐
│ FastAPI API Gateway (Auth & RLS) │
└────────────────┬────────────────┘
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
┌──────────────┐   ┌─────────────────────────────┐
│ REST/Service │   │ Multi-Agent Orchestrator     │
│ Endpoints    │   │ (Stateful Intent & Plan)    │
└──────┬───────┘   └──────────────┬──────────────┘
       │                          │
       │     ┌────────────────────┘
       ▼     ▼
┌─────────────────────────────────┐
│ Deterministic Business Services │
│ (Assignment, Analytics, CRM)    │
└────────────────┬────────────────┘
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
┌──────────────┐   ┌─────────────────────────────┐
│ PostgreSQL   │   │ Outbox / Event Broadcaster  │
│ (RLS Scoped) │   │ (SSE Activity Feed Stream)  │
└──────────────┘   └─────────────────────────────┘
```
