#!/usr/bin/env python3
from pathlib import Path
from sentinelhub import BBox, CRS, DataCollection, SHConfig, SentinelHubCatalog

config = SHConfig()
for line in Path(".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        if k.strip() == "SH_CLIENT_ID":
            config.sh_client_id = v.strip()
        if k.strip() == "SH_CLIENT_SECRET":
            config.sh_client_secret = v.strip()
config.sh_base_url = "https://sh.dataspace.copernicus.eu"
config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

hingna_bbox = BBox((78.965, 21.095, 79.005, 21.135), crs=CRS.WGS84)

catalog = SentinelHubCatalog(config=config)
data_collection = DataCollection.SENTINEL2_L2A.define_from(
    name="s2l2a", service_url="https://sh.dataspace.copernicus.eu"
)

def search_window(label, start_date, end_date):
    print(f"\n=======================================================")
    print(f"  CATALOG SEARCH: {label} ({start_date} to {end_date})")
    print(f"=======================================================")
    results = list(catalog.search(data_collection, bbox=hingna_bbox, time=(start_date, end_date)))
    print(f"Total scenes found: {len(results)}\n")
    
    rows = []
    for r in results:
        p = r.get("properties", {})
        dt = p.get("datetime", "N/A")
        cc = p.get("eo:cloud_cover", p.get("cloudCover", None))
        sid = r.get("id", "")
        rows.append((dt, cc, sid))
    
    rows.sort(key=lambda x: x[0])
    print(f"{'Idx':<4} | {'Acquisition Date/Time (UTC)':<26} | {'Cloud Cover':<12} | {'Scene ID'}")
    print("-" * 85)
    for idx, (dt, cc, sid) in enumerate(rows, 1):
        cc_val = f"{cc:.2f}%" if isinstance(cc, (int, float)) else str(cc)
        print(f"{idx:<4} | {dt:<26} | {cc_val:<12} | {sid}")
        
    valid_cc = [r for r in rows if isinstance(r[1], (int, float))]
    valid_cc.sort(key=lambda x: (x[1], x[0]))
    print(f"\nTop 5 Clearest Scenes for {label}:")
    for rank, (dt, cc, sid) in enumerate(valid_cc[:5], 1):
        print(f"  [{rank}] {dt} -> Cloud Cover: {cc:.4f}% | {sid}")
    return rows

search_window("HINGNA 2022 (BEFORE)", "2022-01-01", "2022-03-31")
search_window("HINGNA 2025 (AFTER - WIDE JAN-JUN)", "2025-01-01", "2025-06-30")
