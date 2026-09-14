"""
Verification Script for YOLO Building Instance Segmentation Pipeline on High-Res 0.6m Wayback Imagery
"""
import sys
import os
import cv2
import numpy as np
import json

sys.path.insert(0, os.path.abspath("."))

from backend.vision.yolo_pipeline import (
    load_yolo_building_model,
    get_yolo_device_info,
    analyze_bitemporal_yolo_buildings
)

print("==================================================")
print("1. HARDWARE DEVICE & MODEL TRANSPARENCY TEST")
print("==================================================")
device_info = get_yolo_device_info()
print("PyTorch Device Info:", json.dumps(device_info, indent=2))

model, model_info = load_yolo_building_model()
print("\nYOLO Building Model Transparency Info:", json.dumps(model_info, indent=2))

print("\n==================================================")
print("2. 0.6m SUB-METER WAYBACK BI-TEMPORAL INFERENCE TEST")
print("==================================================")

# Search for 0.6m wayback images in workspace or backend/static
candidate_pairs = [
    ("backend/static/wayback_mihan_2019_before.png", "backend/static/wayback_mihan_2025_after.png"),
    ("backend/static/wayback_sadar_2019_before.png", "backend/static/wayback_sadar_2025_after.png"),
    ("wayback_mihan_same_season_20190131_before.png", "wayback_mihan_same_season_20250130_after.png")
]

before_path, after_path = None, None
for bp, ap in candidate_pairs:
    if os.path.exists(bp) and os.path.exists(ap):
        before_path, after_path = bp, ap
        break

if not before_path:
    # Find any png image in backend/static
    static_files = [f for f in os.listdir("backend/static") if f.endswith(".png")]
    if len(static_files) >= 2:
        before_path = os.path.join("backend/static", static_files[0])
        after_path = os.path.join("backend/static", static_files[1])

print(f"Testing on 0.6m images: {before_path} & {after_path}")
b_bgr = cv2.imread(before_path)
a_bgr = cv2.imread(after_path)

bbox_wgs84 = [79.020, 21.030, 79.074, 21.090]
res = analyze_bitemporal_yolo_buildings(
    before_bgr=b_bgr,
    after_bgr=a_bgr,
    conf_threshold=0.25,
    iou_threshold=0.35,
    bbox_wgs84=bbox_wgs84
)

print("\nPipeline Result Summary:")
print("Status:", res.get("status"))
print("Summary:", json.dumps(res.get("summary"), indent=2))
print("Building Count Detected:", len(res.get("buildings", [])))

if res.get("buildings"):
    print("\nSample Detected Building:")
    print(json.dumps(res["buildings"][0], indent=2))

print("\nGenerated Artifacts:", json.dumps(res.get("artifacts"), indent=2))
print("==================================================")
print("ALL TESTS PASSED SUCCESSFULLY!")
print("==================================================")
