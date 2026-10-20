import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from graph import create_workflow
from state import SelfHealingState

logger = logging.getLogger("api")
app_api = FastAPI(title="Nexthink Self-Healing Agent API", version="1.0.0")

# Enable CORS for frontend connection
app_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global checkpointer for thread persistence across requests
workflow_app = create_workflow()

class TriggerPayload(BaseModel):
    case_id: Optional[str] = "CASE-20261015-0006"
    device: Optional[str] = "KT-LAP-FIN-01"
    operating_system: Optional[str] = "Windows 11 Enterprise"
    employee: Optional[str] = "Priya Raman"
    department: Optional[str] = "Finance"
    problem_name: str = Field(..., example="Outlook Application Crash Loop (Corrupted Profile)")
    crash_count: Optional[int] = 9
    evidence: Optional[str] = "OUTLOOK.EXE faulting module olmapi32.dll"

class ApprovalPayload(BaseModel):
    decision: str = Field(..., example="APPROVED") # APPROVED or REJECTED
    comment: Optional[str] = "Approved by IT administrator"
    approver: Optional[str] = "admin_priya"

@app_api.get("/")
def health_check():
    return {"status": "ok", "service": "Nexthink Self-Healing LangGraph Agent"}

@app_api.post("/api/trigger")
def trigger_agent(
    payload: TriggerPayload,
    x_webhook_secret: Optional[str] = Header(None)
):
    """Replaces Lyzr Webhook Trigger Node (33bd962956fcdfec57a51f2ce1c780f92489cc1605fd436cb97f98c8419d0bbb)"""
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state: SelfHealingState = {
        "case_id": payload.case_id or f"CASE-{str(uuid.uuid4())[:8]}",
        "thread_id": thread_id,
        "device": payload.device or "KT-LAP-FIN-01",
        "operating_system": payload.operating_system or "Windows 11 Enterprise",
        "employee": payload.employee or "Priya Raman",
        "department": payload.department or "Finance",
        "problem": {
            "error_name": payload.problem_name,
            "details": payload.evidence or ""
        },
        "crash_count": payload.crash_count or 1,
        "observed_evidence": payload.evidence or ""
    }

    # Execute workflow until completion or until approval is needed
    try:
        final_state = workflow_app.invoke(initial_state, config=config)
        return {
            "thread_id": thread_id,
            "status": "COMPLETED" if final_state.get("validation_status") == "HEALTHY" else "ESCALATED_OR_PENDING",
            "governance_decision": final_state.get("governance_decision"),
            "remediation_status": final_state.get("remediation_status"),
            "validation_status": final_state.get("validation_status"),
            "incidents": final_state.get("incidents", []),
            "validation_report": final_state.get("validation_report")
        }
    except Exception as e:
        logger.exception(f"Workflow execution encountered: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app_api.post("/api/approval/{thread_id}")
def submit_approval(thread_id: str, payload: ApprovalPayload):
    """Submits human approval decision and resumes the workflow thread."""
    config = {"configurable": {"thread_id": thread_id}}
    
    # Update state with approval
    update_data = {
        "human_approval_status": payload.decision.upper(),
        "human_approval_comment": payload.comment,
        "approver": payload.approver
    }

    try:
        final_state = workflow_app.invoke(update_data, config=config)
        return {
            "thread_id": thread_id,
            "decision_applied": payload.decision.upper(),
            "remediation_status": final_state.get("remediation_status"),
            "validation_status": final_state.get("validation_status"),
            "validation_report": final_state.get("validation_report"),
            "incidents": final_state.get("incidents", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app_api.get("/api/status/{thread_id}")
def get_status(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    state = workflow_app.get_state(config)
    if not state or not state.values:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {
        "thread_id": thread_id,
        "current_values": state.values,
        "next_nodes": list(state.next)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app_api, host="0.0.0.0", port=8000)
