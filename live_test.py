import requests
import json
import sys

URL = "http://localhost:8000/api/acquire-imagery"
payload = {
    "location_id": "retrieval-S2_NANDANVAN_20250226",
    "location_name": "Nandanvan Test",
    "lat": 21.135,
    "lng": 79.129,
    "bbox": [79.105, 21.111, 79.153, 21.159],
    "before_date": "2022-02-22",
    "after_date": "2025-02-26"
}

print("Running POST to /api/acquire-imagery")
resp = requests.post(URL, json=payload)
print(f"Status Code: {resp.status_code}")
try:
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print(resp.text)
