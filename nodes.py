import logging
from typing import Dict, Any
from state import SelfHealingState
from services import create_servicenow_incident, trigger_reset_demo

logger = logging.getLogger(__name__)

def telemetry_diagnostic_agent(state: SelfHealingState) -> Dict[str, Any]:
    """Node 1: Telemetry Diagnostic Agent
    Analyzes telemetry, device health metrics, and event logs.
    """
    problem = state.get("problem", {})
    error_name = problem.get("error_name", "Unknown Endpoint Issue")
    device = state.get("device", "KT-LAP-FIN-01")
    crashes = state.get("crash_count", 9)

    logger.info(f"[Telemetry Diagnostic Agent] Diagnosing issue for device {device}: {error_name}")

    if "System Drive" in error_name:
        summary = (
            f"Diagnostic Report for {device}: Disk C:\\ usage is at 99.4% (only 420MB remaining). "
            f"Identified 18.2GB of purgeable temporary files and obsolete system caches."
        )
    elif "Outlook" in error_name:
        summary = (
            f"Diagnostic Report for {device}: Application OUTLOOK.EXE experienced {crashes} crashes "
            f"within 24 hours. Primary faulting module: olmapi32.dll (Event ID 1000/1002). "
            f"Root cause: Corrupted offline data file (.ost) & registry profile discrepancy."
        )
    else:
        summary = f"Diagnostic Report for {device}: Unrecognized system alert '{error_name}'."

    return {
        "diagnostic_summary": summary,
        "case_id": state.get("case_id", "CASE-20261015-0006"),
        "device": device,
        "employee": state.get("employee", "Priya Raman"),
        "department": state.get("department", "Finance"),
        "operating_system": state.get("operating_system", "Windows 11 Enterprise")
    }

def guardrail_decision_agent(state: SelfHealingState) -> Dict[str, Any]:
    """Node 2: Guardrail Decision Agent
    Evaluates governance policies, blast radius, and automation risk.
    """
    error_name = state.get("problem", {}).get("error_name", "")
    logger.info(f"[Guardrail Decision Agent] Evaluating policies for: {error_name}")

    if error_name == "System Drive Storage Exhaustion":
        decision = "SAFE_FOR_AUTOMATION"
        reasons = [
            "Standard maintenance runbook (RB-WIN-014)",
            "Low blast radius: purges only non-locked temporary directories and update caches",
            "Pre-approved by IT Operations Security Policy"
        ]
    elif error_name == "Outlook Application Crash Loop (Corrupted Profile)":
        decision = "HUMAN_APPROVAL_REQUIRED"
        reasons = [
            "User data boundary: involves resetting mail profile cache",
            "High executive / departmental visibility (Finance user)",
            "Governance Policy GOV-IT-204 mandates IT support or user sign-off prior to profile rebuild"
        ]
    else:
        decision = "ESCALATE"
        reasons = ["Issue not recognized under self-healing catalog. Manual engineer triage required."]

    return {
        "governance_decision": decision,
        "guardrail_reasons": reasons
    }

def decision_router(state: SelfHealingState) -> str:
    """Conditional Switch Node (Matches Lyzr 'Decision' Switch rules)
    - If problem.error_name == 'System Drive Storage Exhaustion' -> safe_for_automation
    - If problem.error_name == 'Outlook Application Crash Loop (Corrupted Profile)' -> human_approval
    - Else -> escalation
    """
    error_name = state.get("problem", {}).get("error_name", "")
    logger.info(f"[Decision Switch] Routing based on error_name: '{error_name}'")

    if error_name == "System Drive Storage Exhaustion":
        return "safe_automation_snow_incident"
    elif error_name == "Outlook Application Crash Loop (Corrupted Profile)":
        return "human_approval_snow_incident"
    else:
        return "escalation_node"

def safe_automation_snow_incident(state: SelfHealingState) -> Dict[str, Any]:
    """Node 3A: Safe for Automation ServiceNow Incident"""
    device = state.get("device", "UNKNOWN-DEV")
    problem = state.get("problem", {}).get("error_name", "Storage Exhaustion")
    
    short_desc = f"[AUTO_HEALING_INITIATED] {problem} on {device}"
    desc = (
        f"Autonomous Remediation Initiated.\n"
        f"Device: {device}\n"
        f"Problem: {problem}\n"
        f"Governance: SAFE_FOR_AUTOMATION\n"
        f"Diagnostic: {state.get('diagnostic_summary', '')}"
    )

    incident = create_servicenow_incident(
        short_description=short_desc,
        description=desc,
        urgency="3",
        impact="3",
        category="Hardware",
        subcategory="Storage",
        comments="System drive space exhaustion remediation triggered automatically."
    )
    
    incidents = list(state.get("incidents", []))
    incidents.append(incident)
    return {"incidents": incidents}

def human_approval_snow_incident(state: SelfHealingState) -> Dict[str, Any]:
    """Node 3B: Human Approval ServiceNow Incident"""
    device = state.get("device", "KT-LAP-FIN-01")
    employee = state.get("employee", "Priya Raman")
    dept = state.get("department", "Finance")
    problem = state.get("problem", {}).get("error_name", "Outlook Application Crash Loop")

    short_desc = f"[APPROVAL_PENDING] {problem} - {employee} ({device})"
    desc = (
        f"Governance Decision: HUMAN_APPROVAL_REQUIRED.\n\n"
        f"Case ID: {state.get('case_id', 'CASE-20261015-0006')}\n"
        f"Device: {device} ({dept})\n"
        f"Problem: {problem}\n"
        f"Summary: {state.get('diagnostic_summary', '')}\n\n"
        f"Awaiting administrator/user approval before rebuilding corrupted profile."
    )

    incident = create_servicenow_incident(
        short_description=short_desc,
        description=desc,
        urgency="2",
        impact="2",
        category="Software",
        subcategory="Email",
        comments="Incident logged. Awaiting human authorization to proceed with profile repair."
    )

    incidents = list(state.get("incidents", []))
    incidents.append(incident)
    return {"incidents": incidents}

def wait_for_human_approval(state: SelfHealingState) -> Dict[str, Any]:
    """Node 4: Wait for Human Approval (Human-in-the-Loop)
    In interactive/LangGraph execution, this node receives or inspects approval status.
    If not yet provided, modern LangGraph pauses execution using interrupt().
    """
    approval = state.get("human_approval_status")
    logger.info(f"[Wait for Human Approval] Current status: {approval}")
    
    # If using LangGraph interrupt function dynamically:
    if not approval or approval == "PENDING":
        try:
            from langgraph.types import interrupt
            user_response = interrupt({
                "action": "human_approval_required",
                "case_id": state.get("case_id"),
                "device": state.get("device"),
                "problem": state.get("problem", {}).get("error_name"),
                "prompt": "Do you authorize automated remediation (profile rebuild) for this endpoint? (APPROVED / REJECTED)"
            })
            if isinstance(user_response, dict):
                return {
                    "human_approval_status": user_response.get("status", "REJECTED"),
                    "human_approval_comment": user_response.get("comment", "Responded via interrupt"),
                    "approver": user_response.get("approver", "human_agent")
                }
            elif isinstance(user_response, str):
                return {"human_approval_status": user_response.upper()}
        except (ImportError, Exception):
            pass

    return {"human_approval_status": approval or "REJECTED"}

def approval_router(state: SelfHealingState) -> str:
    """Branch from Wait for Human Approval:
    - If APPROVED -> remediation_execution_agent
    - If REJECTED -> escalation_servicenow_incident
    """
    status = state.get("human_approval_status", "").upper()
    logger.info(f"[Approval Router] Approval status is: {status}")
    if status == "APPROVED":
        return "remediation_execution_agent"
    return "escalation_snow_incident"

def escalation_node(state: SelfHealingState) -> Dict[str, Any]:
    """Node 5: Escalation (NoOp in Lyzr JSON)"""
    logger.info("[Escalation Node] Passing to Escalation ServiceNow Incident.")
    return {}

def escalation_servicenow_incident(state: SelfHealingState) -> Dict[str, Any]:
    """Node 6: Escalation ServiceNow Incident
    Matches the exact payload structure from the Lyzr JSON!
    """
    problem_name = state.get("problem", {}).get("error_name", "Outlook Application Crash Loop (Corrupted Profile)")
    device = state.get("device", "KT-LAP-FIN-01")
    employee = state.get("employee", "Priya Raman")
    dept = state.get("department", "Finance")
    case_id = state.get("case_id", "CASE-20261015-0006")
    crashes = state.get("crash_count", 9)
    approval_status = state.get("human_approval_status", "REJECTED")

    short_desc = f"[AUTOMATION_BLOCKED] {problem_name} - Human Approval Rejected"
    desc = (
        f"{problem_name} on endpoint {device}.\n\n"
        f"Incident Details:\n"
        f"- Case ID: {case_id}\n"
        f"- Device: {device}\n"
        f"- Operating System: {state.get('operating_system', 'Windows 11 Enterprise')}\n"
        f"- Employee: {employee}\n"
        f"- Department: {dept}\n"
        f"- Problem: {problem_name}\n"
        f"- Observed Evidence: OUTLOOK.EXE repeatedly crashed with faulting module olmapi32.dll. "
        f"Application Hang events (Event ID 1002) were also recorded.\n"
        f"- Crash Count: {crashes} in the last 24 hours\n\n"
        f"Governance Decision: HUMAN_APPROVAL_REQUIRED\n\n"
        f"Approval Status: {approval_status}\n\n"
        f"Reason for Escalation: The remediation request was rejected by the human approver. "
        f"Automated remediation must not proceed. The incident is escalated for manual investigation and resolution.\n\n"
        f"Required Action: The IT support team must investigate the Outlook profile and application crashes, "
        f"determine the appropriate corrective action, and resolve the incident manually."
    )

    incident = create_servicenow_incident(
        short_description=short_desc,
        description=desc,
        urgency="2",
        impact="2",
        category="Software",
        subcategory="Email",
        comments="Escalated automatically from the Endpoint Self-Healing workflow because human approval was rejected. No automated remediation was executed."
    )

    incidents = list(state.get("incidents", []))
    incidents.append(incident)
    return {
        "incidents": incidents,
        "remediation_status": "SKIPPED",
        "validation_status": "DEGRADED",
        "validation_report": "Remediation halted due to escalation. Ticket assigned to Tier 2 IT Desktop Support."
    }

# Alias for graph node consistency
escalation_snow_incident = escalation_servicenow_incident

def remediation_execution_agent(state: SelfHealingState) -> Dict[str, Any]:
    """Node 7: Remediation Execution Agent"""
    problem_name = state.get("problem", {}).get("error_name", "")
    device = state.get("device", "KT-LAP-FIN-01")
    logger.info(f"[Remediation Execution Agent] Executing automated healing for: {problem_name}")

    if "System Drive" in problem_name:
        log = (
            f"Remediation Log for {device}:\n"
            f"1. Terminated orphan temp worker processes.\n"
            f"2. Purged %TEMP% and %SystemRoot%\\Temp (12.4 GB reclaimed).\n"
            f"3. Cleared SoftwareDistribution download cache (5.1 GB reclaimed).\n"
            f"Total Space Reclaimed: 17.5 GB. C: drive free space is now healthy (22.1 GB free)."
        )
    else:
        log = (
            f"Remediation Log for {device}:\n"
            f"1. Safely halted lingering OUTLOOK.EXE background instances.\n"
            f"2. Archived existing corrupted OST cache to C:\\Users\\Backup\\Archive.ost.\n"
            f"3. Purged corrupted MAPI profile subkeys.\n"
            f"4. Reinitialized fresh Exchange profile and generated clean OST cache sync.\n"
            f"Remediation status: Successfully completed."
        )

    return {
        "remediation_status": "SUCCESS",
        "remediation_log": log
    }

def reset_demo_http_node(state: SelfHealingState) -> Dict[str, Any]:
    """Node 8: HTTP Request (Reset Demo API call)"""
    logger.info("[HTTP Request Node] Triggering https://pif.ai-kaar.tech/api/reset-demo")
    result = trigger_reset_demo()
    return {"reset_demo_response": result}

def post_healing_validation_agent(state: SelfHealingState) -> Dict[str, Any]:
    """Node 9: Post-Healing Validation Agent"""
    problem_name = state.get("problem", {}).get("error_name", "")
    device = state.get("device", "KT-LAP-FIN-01")
    logger.info(f"[Post-Healing Validation Agent] Validating recovery on {device}")

    if "System Drive" in problem_name:
        report = (
            f"Endpoint Validation PASSED for {device}:\n"
            f"- C:\\ Drive Available Space: 22.1 GB (Threshold: >5 GB) [PASS]\n"
            f"- Storage telemetry alert resolved. Endpoint self-healing verified."
        )
    else:
        report = (
            f"Endpoint Validation PASSED for {device}:\n"
            f"- Outlook launched cleanly in diagnostic sub-mode with zero crash signals [PASS]\n"
            f"- olmapi32.dll fault count: 0 (last 10 minutes) [PASS]\n"
            f"- Mail sync health: 100% synchronized [PASS]\n"
            f"Workflow successfully healed endpoint."
        )

    return {
        "validation_status": "HEALTHY",
        "validation_report": report
    }
