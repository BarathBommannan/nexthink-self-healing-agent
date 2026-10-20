from typing import Optional, Dict, Any, List, Literal
from typing_extensions import TypedDict

class EndpointProblem(TypedDict, total=False):
    error_name: str
    category: str
    details: str
    recommended_action: str

class SelfHealingState(TypedDict, total=False):
    # Workflow Metadata
    case_id: str
    thread_id: str
    timestamp: str

    # Endpoint Telemetry
    device: str
    operating_system: str
    employee: str
    department: str
    problem: EndpointProblem
    crash_count: int
    observed_evidence: str

    # Agent Diagnoses & Guardrail Outputs
    diagnostic_summary: str
    governance_decision: Literal["SAFE_FOR_AUTOMATION", "HUMAN_APPROVAL_REQUIRED", "ESCALATE"]
    guardrail_reasons: List[str]

    # Human-in-the-Loop Approval
    human_approval_status: Optional[Literal["APPROVED", "REJECTED", "PENDING"]]
    human_approval_comment: Optional[str]
    approver: Optional[str]

    # External Integrations (ServiceNow, Reset Demo)
    incidents: List[Dict[str, Any]]
    reset_demo_response: Optional[Dict[str, Any]]

    # Remediation & Post-Validation
    remediation_status: Optional[Literal["SUCCESS", "FAILED", "SKIPPED"]]
    remediation_log: Optional[str]
    validation_status: Optional[Literal["HEALTHY", "DEGRADED", "FAILED"]]
    validation_report: Optional[str]

    # Error handling
    error_message: Optional[str]
