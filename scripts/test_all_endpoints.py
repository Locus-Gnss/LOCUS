import sys
import json
import urllib.request
import urllib.parse

BASE_URL = "http://127.0.0.1:8000"

def get(path):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read()

def post(path, payload):
    url = f"{BASE_URL}{path}"
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status, resp.read()

endpoints = [
    ("Root Endpoint", "GET", "/", None),
    ("Swagger Docs", "GET", "/docs", None),
    ("System Health", "GET", "/api/health", None),
    ("List Events", "GET", "/api/events", None),
    ("Get Event Detail", "GET", "/api/events/evt_4_220", None),
    ("Get Evidence Bundle", "GET", "/api/evidence/evt_4_220", None),
    ("Latest Telemetry", "GET", "/api/telemetry/latest", None),
    ("Telemetry History", "GET", "/api/telemetry/history?limit=10", None),
    ("Latest Features", "GET", "/api/features/latest", None),
    ("Alerts List", "GET", "/api/alerts", None),
    ("Specific Alert", "GET", "/api/alerts/ALT-evt_4_220", None),
    ("Agents Status", "GET", "/api/agents/status", None),
    ("RAG Regulatory Query", "POST", "/api/rag/query", {"query": "ICAO spoofing threshold"}),
    ("Natural Language SOC Query", "POST", "/api/query", {"query": "What is the status of evt_4_220?", "event_id": "evt_4_220"}),
    ("SOC Agent Deliberation", "POST", "/api/soc/deliberate", {"event_id": "evt_4_220"}),
]

all_pass = True
for name, method, path, payload in endpoints:
    try:
        if method == "GET":
            status, body = get(path)
        else:
            status, body = post(path, payload)
        
        # Verify JSON if applicable
        is_json = False
        try:
            parsed = json.loads(body)
            is_json = True
            preview = str(parsed)[:80] + "..." if len(str(parsed)) > 80 else str(parsed)
        except Exception:
            preview = f"HTML/Text ({len(body)} bytes)"
            
        if status == 200:
            print(f"[PASS] {name:<30} {method:<4} {path:<30} => Status {status} | {preview}")
        else:
            print(f"[FAIL] {name:<30} {method:<4} {path:<30} => Status {status}")
            all_pass = False
    except Exception as e:
        print(f"[ERROR] {name:<30} {method:<4} {path:<30} => Error: {e}")
        all_pass = False

print("\n" + ("="*60))
if all_pass:
    print("ALL 15 API ENDPOINTS PASSED VERIFICATION!")
else:
    print("SOME ENDPOINTS FAILED!")
print("="*60)
sys.exit(0 if all_pass else 1)
