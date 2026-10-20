import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_storage():
    print("\n" + "="*60)
    print("TEST 1: Safe for Automation (System Drive Storage Exhaustion)")
    print("="*60)
    payload = {
        "problem_name": "System Drive Storage Exhaustion",
        "device": "KT-LAP-FIN-01",
        "employee": "Priya Raman",
        "department": "Finance",
        "evidence": "Disk C: usage at 99.4%"
    }
    resp = requests.post(f"{BASE_URL}/api/trigger", json=payload)
    print(f"Status Code: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))

def test_outlook():
    print("\n" + "="*60)
    print("TEST 2: Human Approval Required (Outlook Crash Loop)")
    print("="*60)
    payload = {
        "problem_name": "Outlook Application Crash Loop (Corrupted Profile)",
        "device": "KT-LAP-FIN-01",
        "employee": "Priya Raman",
        "department": "Finance",
        "crash_count": 9,
        "evidence": "OUTLOOK.EXE faulting module olmapi32.dll"
    }
    resp = requests.post(f"{BASE_URL}/api/trigger", json=payload)
    print(f"Status Code: {resp.status_code}")
    res = resp.json()
    print(json.dumps(res, indent=2))
    
    thread_id = res.get("thread_id")
    if thread_id and res.get("status") == "ESCALATED_OR_PENDING":
        print(f"\n[+] Approving remediation for thread: {thread_id}...")
        approval_payload = {
            "decision": "APPROVED",
            "comment": "Approved by IT desktop support",
            "approver": "admin_priya"
        }
        app_resp = requests.post(f"{BASE_URL}/api/approval/{thread_id}", json=approval_payload)
        print(f"Approval Status Code: {app_resp.status_code}")
        print(json.dumps(app_resp.json(), indent=2))

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "outlook":
        test_outlook()
    else:
        test_storage()
