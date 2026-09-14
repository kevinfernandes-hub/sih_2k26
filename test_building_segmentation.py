"""
Standalone Test Script for Building Segmentation (Stage 2A)
Runs keremberke/yolov8s-building-segmentation on a real Nagpur Wayback crop.
"""

import sys
import json
from pathlib import Path
import cv2

# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.building_segmentor import run_building_segmentation, get_inference_device


def main():
    print("=" * 65)
    print("Nagpur EarthWatch — Stage 2A Building Segmentation Test")
    print("=" * 65)

    # 1. Check Inference Device
    dev, dev_name = get_inference_device()
    print(f"[1] Inference Device Detected: {dev} ({dev_name})")

    # 2. Select Real Existing Nagpur Wayback Crop
    # Level 1 crop from MIHAN hotspot 042 (560x560 px real Esri Wayback 0.6m crop)
    real_crop_path = Path("backend/static/hotspot_crops/mihan-042/mihan-042_level1_after.png")
    
    if not real_crop_path.exists():
        # Fallback to detail crop if hotspot crop not found
        real_crop_path = Path("backend/static/wayback_mihan_sameszn_detail_crop.png")
    
    if not real_crop_path.exists():
        print(f"Error: Could not find real Wayback crop at {real_crop_path}")
        sys.exit(1)

    print(f"[2] Selected Real Wayback Crop: {real_crop_path.resolve()}")
    img = cv2.imread(str(real_crop_path))
    print(f"    Image Dimensions: {img.shape[1]}x{img.shape[0]} px (Channels: {img.shape[2]})")

    # 3. Define Output Directory
    output_dir = Path("outputs/yolo_building_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"[3] Target Output Directory: {output_dir.resolve()}")

    # 4. Run Building Segmentation Inference
    print("\n[4] Running YOLOv8s Building Segmentation inference...")
    result = run_building_segmentation(
        image_input=real_crop_path,
        conf_threshold=0.25,
        iou_threshold=0.45,
        imgsz=640,
        output_dir=output_dir,
        pixel_to_meter_scale=None  # Explicitly None because exact geotransform is not calibrated on this PNG crop
    )

    print(f"\n[5] Results Summary:")
    print(f"    - Model: {result['model']}")
    print(f"    - Device Used: {result['device']} ({result['device_description']})")
    print(f"    - Inference Time: {result['inference_time_ms']} ms")
    print(f"    - Total Buildings Detected: {result['total_buildings_detected']}")
    print(f"    - Geospatial Reliable: {result['geospatial_ground_area_reliable']}")
    print(f"    - Calibration Note: {result['geospatial_calibration_notes']}")

    print("\n[6] Detected Buildings List:")
    for det in result["detections"]:
        print(
            f"    * {det['building_id']} | Conf: {det['confidence']:.4f} | "
            f"BBox: {det['bbox_xyxy']} | Pixel Area: {det['pixel_area']} px | "
            f"Ground Area: {det['ground_area_m2']}"
        )

    print("\n[7] Saved Artifacts:")
    for k, v in result["saved_files"].items():
        print(f"    - {k}: {v}")

    print("\n" + "=" * 65)
    print("Stage 2A Building Segmentation Test Completed Successfully!")
    print("=" * 65)


if __name__ == "__main__":
    main()
