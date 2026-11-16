# Multi-Agent Architecture & Governance Specification

## 1. Multi-Agent Ecosystem
The system coordinates 8 specialized AI agents governed by strict access boundaries, structured Pydantic schemas, and deterministic tool bindings. Agents cannot execute arbitrary shell commands, raw unconstrained SQL queries, or direct external network calls.

```mermaid
flowchart TD
    User([Authorized User Request]) --> Orchestrator[Master Orchestrator]
    
    Orchestrator --> IntentClassifier{Classify Intent & Scope}
    
    IntentClassifier -->|Data Query| Agent1[Data Query Agent]
    IntentClassifier -->|Deep Insights| Agent2[Business Insight Agent]
    IntentClassifier -->|CRM Ops & Action| Agent3[CRM Operations Agent]
    IntentClassifier -->|Workload Balance| Agent4[Workload Optimization Agent]
    IntentClassifier -->|Live Monitoring| Agent5[Monitoring Agent]
    IntentClassifier -->|Reporting| Agent6[Reporting Agent]
    IntentClassifier -->|Risk & Anomalies| Agent7[Risk & Anomaly Agent]

    Agent1 --> Tools[Approved Typed Tools & Governed Services]
    Agent2 --> Tools
    Agent3 --> Approval{Manager Approval Required?}
    Agent4 --> Approval
    Agent5 --> Tools
    Agent6 --> Tools
    Agent7 --> Tools

    Approval -->|Yes: Consequential Action| Proposal[Draft Proposal / Batch Preview]
    Proposal --> Manager([Manager Review & Approval])
    Manager -->|Approved| ExecService[Deterministic CRM Execution Service]
    Approval -->|No: Read-Only Tool| Tools

    Tools --> Outbox[Event Bus & Outbox]
    ExecService --> Outbox
    Outbox --> SSE[Live Activity Feed Update]
```

## 2. Specialized Agent Roles & Capabilities

### Agent 1: Master Orchestrator
- **Responsibility**: Interprets requests, categorizes intent (`query`, `analysis`, `action`, `monitoring`), checks user role/region permissions, dispatches sub-tasks to specialized agents, aggregates results, and logs the execution session.

### Agent 2: Data Query Agent
- **Responsibility**: Translates natural language questions into authorized database query filters. Strictly applies user's regional/role constraints. Returns exact records with database references.

### Agent 3: Business Insight Agent
- **Responsibility**: Analyzes performance trends, calculates conversion rates across projects and marketing sources, identifies project bottlenecks, and provides explainable insights supported by data references.

### Agent 4: CRM Operations Agent
- **Responsibility**: Manages lead actions, follow-up scheduling, task creations, and status transitions. Produces batch proposals with reasons for each change.

### Agent 5: Workload Optimization Agent
- **Responsibility**: Evaluates employee capacity, project familiarity, regional assignment, pending task backlogs, and conversion efficiency. Recommends optimal lead distribution without ever bypassing human manager approval.

### Agent 6: Monitoring Agent
- **Responsibility**: Tracks CRM sync latency, outbox queue health, error spikes, and recent operational events.

### Agent 7: Reporting Agent
- **Responsibility**: Synthesizes periodic management summaries, employee productivity rankings, and inventory reports in structured JSON/CSV.

### Agent 8: Risk & Anomaly Agent
- **Responsibility**: Detects abnormal patterns (e.g. sudden batch reassignments, unusual authentication spikes, outbox synchronization failures, duplicate leads).
