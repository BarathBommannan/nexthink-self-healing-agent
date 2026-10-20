import uuid
import json
import logging
import sys
from graph import create_workflow

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

def print_separator(title: str):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)

def run_scenario(name: str, initial_state: dict, approve_action: str = None):
    print_separator(f"SCENARIO: {name}")
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    app = create_workflow()

    print(f"[*] Initializing thread: {thread_id}")
    print(f"[*] Problem input: {initial_state.get('problem', {}).get('error_name')}")

    state_to_run = {**initial_state, "thread_id": thread_id}
    if approve_action:
        state_to_run["human_approval_status"] = approve_action

    events = app.stream(state_to_run, config=config, stream_mode="values")
    
    last_state = None
    for event in events:
        last_state = event

    print("\n[+] Execution Finished.")
    print(f"    - Governance Decision: {last_state.get('governance_decision')}")
    print(f"    - Human Approval:     {last_state.get('human_approval_status', 'N/A')}")
    print(f"    - Remediation Status: {last_state.get('remediation_status', 'N/A')}")
    print(f"    - Validation Status:  {last_state.get('validation_status', 'N/A')}")
    print(f"    - Incidents Logged:   {len(last_state.get('incidents', []))}")
    for idx, inc in enumerate(last_state.get('incidents', []), 1):
        print(f"       {idx}. [{inc.get('incident_number', 'INC-MOCK')}] {inc.get('payload', {}).get('short_description')}")
    
    if last_state.get("validation_report"):
        print(f"\n[+] Final Validation Report:\n{last_state.get('validation_report')}")

if __name__ == "__main__":
    print("\n🚀 NEXTHINK SELF-HEALING LANGGRAPH DEMO RUNNER 🚀")

    # 1. Safe for Automation Branch
    run_scenario(
        name="1. Safe for Automation (System Drive Storage Exhaustion)",
        initial_state={
            "case_id": "CASE-20261015-0001",
            "device": "KT-LAP-FIN-01",
            "employee": "Priya Raman",
            "department": "Finance",
            "operating_system": "Windows 11 Enterprise",
            "problem": {
                "error_name": "System Drive Storage Exhaustion",
                "category": "Storage"
            },
            "crash_count": 0
        }
    )

    # 2. Human Approval -> APPROVED Branch
    run_scenario(
        name="2. Human Approval -> APPROVED (Outlook Profile Rebuild)",
        initial_state={
            "case_id": "CASE-20261015-0006",
            "device": "KT-LAP-FIN-01",
            "employee": "Priya Raman",
            "department": "Finance",
            "operating_system": "Windows 11 Enterprise",
            "problem": {
                "error_name": "Outlook Application Crash Loop (Corrupted Profile)",
                "category": "Email"
            },
            "crash_count": 9
        },
        approve_action="APPROVED"
    )

    # 3. Human Approval -> REJECTED Branch (Escalation)
    run_scenario(
        name="3. Human Approval -> REJECTED (Escalates to ServiceNow Tier 2)",
        initial_state={
            "case_id": "CASE-20261015-0006",
            "device": "KT-LAP-FIN-01",
            "employee": "Priya Raman",
            "department": "Finance",
            "operating_system": "Windows 11 Enterprise",
            "problem": {
                "error_name": "Outlook Application Crash Loop (Corrupted Profile)",
                "category": "Email"
            },
            "crash_count": 9
        },
        approve_action="REJECTED"
    )

    # 4. Unknown Issue -> Fallback Escalation
    run_scenario(
        name="4. Unrecognized Error -> Automatic Escalation",
        initial_state={
            "case_id": "CASE-20261015-9999",
            "device": "KT-LAP-EXEC-02",
            "employee": "John Doe",
            "department": "Executive",
            "operating_system": "Windows 11 Enterprise",
            "problem": {
                "error_name": "Kernel Blue Screen Crash 0x0000003B",
                "category": "OS Kernel"
            },
            "crash_count": 3
        }
    )