import requests

tests = [
    {"query": "vegetation loss", "top_k": 3},
    {"query": "new construction", "top_k": 3},
    {"query": "urban expansion", "top_k": 3},
    {"query": "water body reduction", "top_k": 3},
    {"query": "land clearance", "top_k": 3}
]

for t in tests:
    print(f"Testing {t['query']}...")
    try:
        r = requests.post("http://localhost:8000/api/discover-and-verify", json=t)
        res = r.json()
        print(f"  Mode: {res.get('mode')}")
        hotspots = res.get('ranked_hotspots', [])
        print(f"  Hotspots found: {len(hotspots)}")
        if hotspots:
            for i, h in enumerate(hotspots[:1]):
                print(f"    Top: {h['location_name']}, Score: {h['evidence_score']}")
                yolo = h.get('yolo_analysis')
                if yolo:
                    print(f"    YOLO Available: {yolo.get('available')}, New: {yolo.get('summary', {}).get('new_count')}")
    except Exception as e:
        print("  Error:", e)
