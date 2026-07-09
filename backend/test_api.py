"""End-to-end test: report -> AI process -> route -> retrieve."""
import httpx
import json

BASE = "http://127.0.0.1:8000"


def log(label: str, resp: httpx.Response):
    print(f"\n=== {label} ===")
    print(f"Status: {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2, default=str))
    except Exception:
        print(resp.text)


# 1. Submit a user report
resp = httpx.post(f"{BASE}/report", json={
    "source_type": "user",
    "source_name": "employee",
    "device_ip": "192.168.1.100",
    "description": "My computer locked up and showed a red screen with a ransom note.",
    "base_severity": "Pending",
    "conversation_log": [
        {"role": "user", "content": "My computer locked up"}
    ]
}, timeout=30)
log("STEP 1 — Submit Report", resp)
data = resp.json()
incident_id = data.get("incident_id")

if not incident_id:
    print("\nFAILED: No incident_id returned")
    exit(1)

# 2. Trigger AI processing
resp = httpx.post(f"{BASE}/ai/process", json={
    "incident_id": incident_id
}, timeout=120)
log("STEP 2 — AI Processing", resp)

# 3. Route the incident (Cybersec team actions)
resp = httpx.post(f"{BASE}/route", json={
    "incident_id": incident_id,
    "action_tasks": ["Isolate machine from network", "Reset credentials"],
    "affected_users": ["john.doe@company.com"],
    "final_admin_report": "The attack has been contained. User notified."
}, timeout=30)
log("STEP 3 — Route Incident", resp)

# 4. Retrieve the final incident
resp = httpx.get(f"{BASE}/incident/{incident_id}", timeout=30)
log("STEP 4 — Get Final Incident", resp)

print("\n✅ Done — all endpoints tested successfully")
