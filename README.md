# Nexthink Self-Healing Agent (LangGraph Migration)

Re-implementation of the **Lyzr.ai "Nexthink Self Healing - PIF"** agent workflow into an enterprise-ready, reliable **LangGraph** application.

---

## Architecture & Node Mapping

This project maps every single node and edge from your Lyzr JSON into LangGraph components:

| Lyzr Node Name | Lyzr Type / ID | LangGraph Implementation | Description |
| :--- | :--- | :--- | :--- |
| **Trigger** | `lyzr-nodes-base.trigger` | `api.py: /api/trigger` or CLI input | Webhook endpoint receiving Nexthink device telemetry. |
| **Telemetry Diagnostic Agent** | `lyzr.agent` | `nodes.py: telemetry_diagnostic_agent` | Parses logs, crash counts, faulting modules, disk space. |
| **Guardrail Decision agent** | `lyzr.agent` | `nodes.py: guardrail_decision_agent` | Assesses blast radius, policy, and governance decision. |
| **Decision** | `lyzr-nodes-base.switch` | `nodes.py: decision_router` (Conditional Edge) | Exact 3-way branch: Disk Storage vs Outlook Crash vs Escalation. |
| **Safe for Automation ServiceNow Incident** | `httpRequest` | `nodes.py: safe_automation_snow_incident` | Logs initial incident for pre-approved autonomous healing. |
| **Human Approval ServiceNow Incident** | `httpRequest` | `nodes.py: human_approval_snow_incident` | Logs pending approval incident in ServiceNow. |
| **Wait for Human Approval** | `waitForApproval` | `nodes.py: wait_for_human_approval` & `approval_router` | Halts execution until approver submits APPROVED or REJECTED. |
| **Escalation** | `noOp` | `nodes.py: escalation_node` | Escalation passthrough node. |
| **Escalation ServiceNow Incident** | `httpRequest` | `nodes.py: escalation_snow_incident` | Logs urgency 2 / impact 2 manual triage incident. |
| **Remediation Execution Agent** | `lyzr.agent` | `nodes.py: remediation_execution_agent` | Performs self-healing runbook actions. |
| **HTTP Request** | `httpRequest` | `nodes.py: reset_demo_http_node` | Calls `https://pif.ai-kaar.tech/api/reset-demo`. |
| **Post-Healing Validation Agent** | `lyzr.agent` | `nodes.py: post_healing_validation_agent` | Validates health recovery before workflow concludes. |

---

## Why the Lyzr Flow Failed & How LangGraph Fixes It

1. **State Mutation & Missing Keys**: Lyzr's switch node often crashes if `problem.error_name` isn't nested identically. In LangGraph, state is strictly typed with `SelfHealingState` (`TypedDict`).
2. **Brittle External Calls**: If ServiceNow API or the reset demo token failed, Lyzr crashed silently. LangGraph handles network errors cleanly and includes an automatic **Mock / Offline Mode** (`MOCK_EXTERNAL_CALLS=true`) to guarantee your demo never crashes during client meetings.
3. **Approval State Loss**: In Lyzr, `waitForApproval` often loses webhook context. In LangGraph, `MemorySaver` keeps checkpointer state per `thread_id`.

---

## Quick Start for Tomorrow's Meeting

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Instant Demonstration (All 4 Scenarios)
Run the automated test runner to demonstrate the entire workflow across all branches:
```bash
python demo_cli.py
```
This tests:
- **Scenario 1**: Safe for Automation (`System Drive Storage Exhaustion`) -> Autonomous Remediation -> Reset Demo -> Validation PASS.
- **Scenario 2**: Human Approval (`Outlook Crash Loop`) -> Approved -> Remediation -> Validation PASS.
- **Scenario 3**: Human Approval -> Rejected -> ServiceNow Incident Escalated to Tier 2.
- **Scenario 4**: Unknown Incident -> Fallback Escalation.

### 3. Run as a Live Webhook Server (FastAPI)
```bash
uvicorn api:app_api --reload --port 8000
```
- **Trigger an Incident**: `POST http://localhost:8000/api/trigger`
- **Submit Human Approval**: `POST http://localhost:8000/api/approval/{thread_id}`
- **Check Status**: `GET http://localhost:8000/api/status/{thread_id}`
