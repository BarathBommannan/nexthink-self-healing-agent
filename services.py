import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

SERVICENOW_URL = os.getenv("SERVICENOW_URL", "https://dev392294.service-now.com/api/now/table/incident")
SERVICENOW_USER = os.getenv("SERVICENOW_USER", "lyzr_integration")
SERVICENOW_PASSWORD = os.getenv("SERVICENOW_PASSWORD", "")
RESET_DEMO_URL = os.getenv("RESET_DEMO_URL", "https://pif.ai-kaar.tech/api/reset-demo")
RESET_DEMO_TOKEN = os.getenv("RESET_DEMO_TOKEN", "")
MOCK_EXTERNAL_CALLS = os.getenv("MOCK_EXTERNAL_CALLS", "true").lower() in ("true", "1", "yes")

def create_servicenow_incident(
    short_description: str,
    description: str,
    urgency: str = "2",
    impact: str = "2",
    category: str = "Software",
    subcategory: str = "Email",
    comments: Optional[str] = None
) -> Dict[str, Any]:
    """Creates a ServiceNow incident via Table API or returns a mock response if offline."""
    payload = {
        "short_description": short_description,
        "description": description,
        "urgency": urgency,
        "impact": impact,
        "category": category,
        "subcategory": subcategory,
        "comments": comments or "Automated incident from Nexthink Self-Healing LangGraph workflow."
    }

    if MOCK_EXTERNAL_CALLS or not SERVICENOW_PASSWORD:
        mock_inc_number = f"INC00{abs(hash(short_description)) % 100000:05d}"
        logger.info(f"[SIMULATION] ServiceNow Incident created: {mock_inc_number} - {short_description}")
        return {
            "status": "simulated",
            "incident_number": mock_inc_number,
            "sys_id": f"mock_sys_id_{mock_inc_number.lower()}",
            "payload": payload
        }

    try:
        import requests
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        resp = requests.post(
            SERVICENOW_URL,
            auth=(SERVICENOW_USER, SERVICENOW_PASSWORD),
            headers=headers,
            json=payload,
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json().get("result", {})
        return {
            "status": "success",
            "incident_number": data.get("number", "INC-UNKNOWN"),
            "sys_id": data.get("sys_id"),
            "raw": data
        }
    except Exception as e:
        logger.error(f"Failed to post to ServiceNow: {e}. Falling back to simulation.")
        return {
            "status": "fallback_simulated",
            "error": str(e),
            "incident_number": f"INC00{abs(hash(short_description)) % 100000:05d}",
            "payload": payload
        }

def trigger_reset_demo() -> Dict[str, Any]:
    """Calls the reset demo endpoint."""
    if MOCK_EXTERNAL_CALLS:
        logger.info("[SIMULATION] Reset demo endpoint triggered successfully.")
        return {"status": "simulated_success", "message": "Demo reset acknowledged."}

    try:
        import requests
        headers = {
            "Content-Type": "application/json",
            "x-reset-token": RESET_DEMO_TOKEN
        }
        resp = requests.post(RESET_DEMO_URL, headers=headers, json={}, timeout=10)
        return {
            "status": "success" if resp.status_code == 200 else "warning",
            "status_code": resp.status_code,
            "response": resp.text[:200]
        }
    except Exception as e:
        logger.warning(f"Reset demo call failed: {e}")
        return {"status": "error", "message": str(e)}
