import requests
import json
import sys

# 1. Semantic Verification
URL_VERIFY = "http://localhost:8000/api/verify-semantics"
payload_verify = {
    "query": "vegetation loss",
    "location_id": "retrieval-S2_NANDANVAN_20250226"
}

print("Running POST to /api/verify-semantics")
resp = requests.post(URL_VERIFY, json=payload_verify)
print(f"Status Code: {resp.status_code}")
try:
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(resp.text)

# 2. Analysis
URL_ANALYZE = "http://localhost:8000/api/analyze"
payload_analyze = {
    "location_id": "retrieval-S2_NANDANVAN_20250226",
    "tier": "0.6m"
}

print("\nRunning POST to /api/analyze")
resp = requests.post(URL_ANALYZE, json=payload_analyze)
print(f"Status Code: {resp.status_code}")
try:
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(resp.text)

