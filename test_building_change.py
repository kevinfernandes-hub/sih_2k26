"""
Test Harness for Stage 2B Building Change Detection
Compares MIHAN-042 Level 1 Before (2019-01-31) vs After (2025-01-30) Wayback crops.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.building_segmentor import compare_building_change, get_inference_device


def main():
    print("=" * 70)
    print("Nagpur EarthWatch — Stage 2B Building Change Detection Test")
    print("=" * 70)

    # 1. Device Info
    dev, dev_name = get_inference_device()
    print(f"[1] Inference Device: {dev} ({dev_name})")

    # 2. Input Images
    before_path = Path("backend/static/hotspot_crops/mihan-042/mihan-042_level1_before.png")
    after_path = Path("backend/static/hotspot_crops/mihan-042/mihan-042_level1_after.png")

    if not before_path.exists() or not after_path.exists():
        print(f"Error: Required crops not found: {before_path} or {after_path}")
        sys.exit(1)

    print(f"[2] Before Image (2019-01-31): {before_path.resolve()}")
    print(f"    After Image  (2025-01-30): {after_path.resolve()}")

    # 3. Output Directory
    output_dir = Path("outputs/yolo_change_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[3] Target Output Directory: {output_dir.resolve()}")

    # 4. Run Comparison Pipeline
    print("\n[4] Running Bi-Temporal Building Segmentation & Spatial Matching (conf>=0.50)...")
    res = compare_building_change(
        before_image=before_path,
        after_image=after_path,
        conf_threshold=0.50,
        iou_match_threshold=0.35,
        expansion_ratio_threshold=1.35,
        output_dir=output_dir
    )

    summary = res["summary"]
    print(f"\n[5] Summary Metrics:")
    print(f"    - Total Before Detections (2019): {summary['total_before_detections']}")
    print(f"    - Total After Detections (2025):  {summary['total_after_detections']}")
    print(f"    - Classified EXISTING:            {summary['num_existing']}")
    print(f"    - Classified NEW:                 {summary['num_new']}")
    print(f"    - Classified EXPANDED:            {summary['num_expanded']}")
    print(f"    - Classified UNCERTAIN:           {summary['num_uncertain']}")
    print(f"    - Before Building Pixel Area:     {summary['before_building_pixel_area']} px")
    print(f"    - After Building Pixel Area:      {summary['after_building_pixel_area']} px")
    print(f"    - Total Change Pixel Area:        {summary['total_change_pixel_area']} px")
    print(f"    - Ground Area (m²):               {summary['ground_area_m2']} (Explicitly uncalibrated)")
    print(f"    - Total Pipeline Time:            {res['total_inference_and_matching_time_ms']} ms")

    print("\n[6] AFTER Building Records Breakdown:")
    for rec in res["after_building_records"]:
        m_id = rec["matched_before_id"] or "None"
        b_conf_str = f"{rec['before_confidence']:.4f}" if rec['before_confidence'] else "N/A"
        dist_str = f"{rec['centroid_distance_px']:.1f} px" if rec['centroid_distance_px'] else "N/A"
        print(
            f"    * {rec['building_id']} | Status: {rec['status']:<9} | "
            f"After Conf: {rec['after_confidence']:.4f} | Match: {m_id:<8} (Before Conf: {b_conf_str}) | "
            f"IoU: {rec['iou']:.4f} | Dist: {dist_str:<8} | Area: {rec['after_pixel_area']} px | Change: {rec['change_pixel_area']} px"
        )

    print("\n[7] BEFORE Building Records Status:")
    for b_rec in res["before_building_records"]:
        matched_str = "MATCHED IN AFTER" if b_rec["matched_in_after"] else "UNMATCHED / REMOVED"
        print(f"    * {b_rec['building_id']} | Conf: {b_rec['confidence']:.4f} | Area: {b_rec['pixel_area']} px | {matched_str}")

    print("\n[8] Generated Output Artifacts:")
    for k, v in res["saved_files"].items():
        print(f"    - {k}: {v}")

    print("\n" + "=" * 70)
    print("Stage 2B Building Change Detection Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
