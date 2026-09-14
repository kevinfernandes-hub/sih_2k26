"""
Building Segmentation & Bi-Temporal Change Detection Module
Nagpur EarthWatch — Stage 2B Building Footprint Change Engine

Integrates keremberke/yolov8s-building-segmentation to:
1. Detect building footprints on high-resolution Esri Wayback imagery.
2. Spatially compare matched BEFORE vs AFTER crops.
3. Classify building footprints into EXISTING, NEW, EXPANDED, and UNCERTAIN.
4. Generate change masks and 3-panel comparison artifacts.

Geospatial Rule:
- Reports exact pixel areas.
- Sets ground_area_m2 = null (uncalibrated) unless explicit geotransform metadata is present.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

import cv2
import numpy as np
from huggingface_hub import hf_hub_download

# Global model cache to avoid repeated reloading
_MODEL_CACHE: Dict[str, Any] = {}


def get_inference_device() -> Tuple[str, str]:
    """
    Detects whether CUDA GPU is available and returns (device_string, device_name).
    Prioritizes CUDA on NVIDIA RTX 3050 when PyTorch CUDA is enabled.
    """
    try:
        import torch
        if torch.cuda.is_available():
            dev_name = torch.cuda.get_device_name(0)
            return "cuda:0", f"GPU: {dev_name}"
    except ImportError:
        pass
    return "cpu", "CPU"


def load_building_model(
    repo_id: str = "keremberke/yolov8s-building-segmentation",
    filename: str = "best.pt",
    device: Optional[str] = None
) -> Any:
    """
    Loads the building-specific YOLO segmentation checkpoint from Hugging Face / cache.
    """
    from ultralytics import YOLO
    import torch
    global _MODEL_CACHE
    target_device = device or get_inference_device()[0]
    cache_key = f"{repo_id}:{filename}:{target_device}"

    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]

    model_path = hf_hub_download(repo_id=repo_id, filename=filename)
    model = YOLO(model_path)

    if "cuda" in target_device and torch.cuda.is_available():
        model.to(target_device)

    _MODEL_CACHE[cache_key] = model
    return model


class BuildingSegmentor:
    """
    Object-oriented wrapper around the YOLOv8 Building Segmentation pipeline.
    """
    def __init__(
        self,
        repo_id: str = "keremberke/yolov8s-building-segmentation",
        filename: str = "best.pt",
        device: Optional[str] = None,
        conf_threshold: float = 0.50
    ):
        self.device, self.device_name = (device, device) if device else get_inference_device()
        self.model = load_building_model(repo_id=repo_id, filename=filename, device=self.device)
        self.conf_threshold = conf_threshold
        self.task = getattr(self.model, "task", "segment")
        self.names = getattr(self.model, "names", {0: "Building"})

    def segment(
        self,
        image_input: Union[str, Path, np.ndarray],
        conf_threshold: Optional[float] = None,
        output_dir: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Runs single-image building segmentation."""
        conf = conf_threshold if conf_threshold is not None else self.conf_threshold
        return run_building_segmentation(
            image_input=image_input,
            conf_threshold=conf,
            device=self.device,
            output_dir=output_dir,
            **kwargs
        )

    def compare(
        self,
        before_image: Union[str, Path, np.ndarray],
        after_image: Union[str, Path, np.ndarray],
        conf_threshold: Optional[float] = None,
        output_dir: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Runs bi-temporal building change comparison."""
        conf = conf_threshold if conf_threshold is not None else self.conf_threshold
        return compare_building_change(
            before_image=before_image,
            after_image=after_image,
            conf_threshold=conf,
            device=self.device,
            output_dir=output_dir,
            **kwargs
        )



def run_building_segmentation(
    image_input: Union[str, Path, np.ndarray],
    conf_threshold: float = 0.25,
    iou_threshold: float = 0.45,
    imgsz: int = 640,
    device: Optional[str] = None,
    output_dir: Optional[Union[str, Path]] = None,
    pixel_to_meter_scale: Optional[float] = None
) -> Dict[str, Any]:
    """
    Runs building segmentation on a single high-resolution satellite image or crop.
    """
    selected_device, device_desc = (device, device) if device else get_inference_device()

    input_file_path = None
    if isinstance(image_input, (str, Path)):
        input_file_path = str(Path(image_input).resolve())
        img_bgr = cv2.imread(input_file_path)
        if img_bgr is None:
            raise FileNotFoundError(f"Could not load image from {image_input}")
    elif isinstance(image_input, np.ndarray):
        img_bgr = image_input
    else:
        raise ValueError("image_input must be a file path or numpy ndarray")

    img_h, img_w = img_bgr.shape[:2]
    model = load_building_model(device=selected_device)

    start_time = time.perf_counter()
    import torch
    if "cuda" in selected_device and torch.cuda.is_available():
        torch.cuda.empty_cache()

    with torch.no_grad():
        results = model.predict(
            source=img_bgr,
            conf=conf_threshold,
            iou=iou_threshold,
            imgsz=imgsz,
            device=selected_device,
            verbose=False,
            retina_masks=True
        )

    inference_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

    result = results[0]
    detections: List[Dict[str, Any]] = []
    combined_mask = np.zeros((img_h, img_w), dtype=np.uint8)

    if result.masks is not None and result.boxes is not None:
        boxes_data = result.boxes.xyxy.cpu().numpy()
        conf_data = result.boxes.conf.cpu().numpy()
        cls_data = result.boxes.cls.cpu().numpy()
        masks_data = result.masks.data.cpu().numpy()

        num_objects = len(boxes_data)

        for i in range(num_objects):
            bbox = [round(float(v), 2) for v in boxes_data[i]]
            conf = round(float(conf_data[i]), 4)
            class_id = int(cls_data[i])
            class_name = model.names.get(class_id, "Building")

            raw_mask = masks_data[i]
            if raw_mask.shape != (img_h, img_w):
                raw_mask = cv2.resize(raw_mask, (img_w, img_h), interpolation=cv2.INTER_NEAREST)

            binary_mask = (raw_mask > 0.5).astype(np.uint8)
            pixel_area = int(np.count_nonzero(binary_mask))
            combined_mask[binary_mask == 1] = 255

            contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            polygons = []
            for cnt in contours:
                if len(cnt) >= 3:
                    poly_pts = cnt.reshape(-1, 2).tolist()
                    polygons.append(poly_pts)

            # Calculate centroid
            M = cv2.moments(binary_mask)
            if M["m00"] > 0:
                cx = round(float(M["m10"] / M["m00"]), 2)
                cy = round(float(M["m01"] / M["m00"]), 2)
            else:
                cx = round((bbox[0] + bbox[2]) / 2.0, 2)
                cy = round((bbox[1] + bbox[3]) / 2.0, 2)

            ground_area_m2 = round(pixel_area * (pixel_to_meter_scale ** 2), 2) if (pixel_to_meter_scale and pixel_to_meter_scale > 0) else None

            detections.append({
                "building_id": f"BLDG-{i + 1:03d}",
                "class_name": class_name,
                "confidence": conf,
                "bbox_xyxy": bbox,
                "centroid": [cx, cy],
                "pixel_area": pixel_area,
                "ground_area_m2": ground_area_m2,
                "polygon_count": len(polygons),
                "polygons": polygons,
                "_binary_mask": binary_mask
            })

    detections.sort(key=lambda d: d["confidence"], reverse=True)

    geospatial_reliable = pixel_to_meter_scale is not None and pixel_to_meter_scale > 0
    geospatial_notes = (
        f"Calibrated scale: {pixel_to_meter_scale:.4f} m/px."
        if geospatial_reliable
        else "Geospatial ground area is currently marked UNAVAILABLE because this image crop does not retain embedded geotransform metadata. Raw pixel_area is reported."
    )

    # Annotated visualization
    annotated_bgr = img_bgr.copy()
    overlay = img_bgr.copy()

    for det in detections:
        for poly in det["polygons"]:
            pts = np.array(poly, dtype=np.int32)
            cv2.fillPoly(overlay, [pts], color=(235, 160, 40))
            cv2.polylines(annotated_bgr, [pts], isClosed=True, color=(255, 220, 80), thickness=2)

        x1, y1, x2, y2 = [int(v) for v in det["bbox_xyxy"]]
        label = f"{det['building_id']} ({det['confidence']:.2f})"
        cv2.rectangle(annotated_bgr, (x1, y1), (x2, y2), (255, 200, 50), 1)
        cv2.putText(annotated_bgr, label, (x1, max(15, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

    annotated_bgr = cv2.addWeighted(overlay, 0.4, annotated_bgr, 0.6, 0)

    saved_files = {}
    if output_dir:
        out_p = Path(output_dir)
        masks_dir = out_p / "masks"
        out_p.mkdir(parents=True, exist_ok=True)
        masks_dir.mkdir(parents=True, exist_ok=True)

        input_path = out_p / "input.jpg"
        annotated_path = out_p / "annotated.jpg"
        combined_mask_path = masks_dir / "combined_mask.png"
        results_json_path = out_p / "results.json"

        cv2.imwrite(str(input_path), img_bgr)
        cv2.imwrite(str(annotated_path), annotated_bgr)
        cv2.imwrite(str(combined_mask_path), combined_mask)

        for det in detections:
            b_id = det["building_id"]
            ind_mask = (det["_binary_mask"] * 255).astype(np.uint8)
            cv2.imwrite(str(masks_dir / f"{b_id}_mask.png"), ind_mask)

        saved_files = {
            "input_image": str(input_path),
            "annotated_image": str(annotated_path),
            "combined_mask": str(combined_mask_path),
            "results_json": str(results_json_path),
            "masks_dir": str(masks_dir)
        }

    # Clean internal binary masks from serializable output
    serializable_detections = []
    for d in detections:
        item = {k: v for k, v in d.items() if k != "_binary_mask"}
        serializable_detections.append(item)

    summary_data = {
        "status": "SUCCESS",
        "scope": "Buildings detected in the high-resolution image",
        "model": "keremberke/yolov8s-building-segmentation",
        "device": selected_device,
        "device_description": device_desc,
        "inference_time_ms": inference_time_ms,
        "image_dimensions": {"width": img_w, "height": img_h, "channels": 3},
        "source_image": input_file_path or "numpy array",
        "total_buildings_detected": len(detections),
        "geospatial_ground_area_reliable": geospatial_reliable,
        "geospatial_calibration_notes": geospatial_notes,
        "detections": serializable_detections,
        "saved_files": saved_files,
        "_raw_detections": detections,
        "_image_bgr": img_bgr
    }

    if output_dir:
        with open(out_p / "results.json", "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in summary_data.items() if not k.startswith("_")}, f, indent=2)

    return summary_data


def compare_building_change(
    before_image: Union[str, Path, np.ndarray],
    after_image: Union[str, Path, np.ndarray],
    conf_threshold: float = 0.50,
    iou_match_threshold: float = 0.35,
    expansion_ratio_threshold: float = 1.35,
    output_dir: Optional[Union[str, Path]] = None,
    device: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compares building segmentations between matched BEFORE and AFTER satellite crops.
    Classifies each AFTER building as:
      - EXISTING: Substantial overlap with a BEFORE building.
      - NEW: Little or no overlap with any BEFORE building.
      - EXPANDED: Overlaps a BEFORE building with substantially larger footprint.
      - UNCERTAIN: Borderline overlap or low confidence detections flagged for audit.

    Generates change masks and comparison visuals (BEFORE | AFTER | NEW/EXPANDED).
    """
    start_total_time = time.perf_counter()

    # 1. Run building segmentation independently on BEFORE and AFTER
    seg_before = run_building_segmentation(
        before_image,
        conf_threshold=conf_threshold,
        device=device
    )
    seg_after = run_building_segmentation(
        after_image,
        conf_threshold=conf_threshold,
        device=device
    )

    img_b = seg_before["_image_bgr"]
    img_a = seg_after["_image_bgr"]
    h, w = img_a.shape[:2]

    # Ensure before image matches after image dimensions
    if img_b.shape[:2] != (h, w):
        img_b = cv2.resize(img_b, (w, h))

    dets_before = seg_before["_raw_detections"]
    dets_after = seg_after["_raw_detections"]

    # 2. Build individual and cumulative binary masks
    b_masks = []
    cum_before_mask = np.zeros((h, w), dtype=np.uint8)
    for b_det in dets_before:
        m = b_det["_binary_mask"]
        if m.shape != (h, w):
            m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
        b_masks.append((b_det, m))
        cum_before_mask[m == 1] = 1

    a_masks = []
    cum_after_mask = np.zeros((h, w), dtype=np.uint8)
    for a_det in dets_after:
        m = a_det["_binary_mask"]
        if m.shape != (h, w):
            m = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
        a_masks.append((a_det, m))
        cum_after_mask[m == 1] = 1

    # 3. Spatial Matching & Classification
    after_records = []
    change_mask = np.zeros((h, w), dtype=np.uint8)
    matched_before_ids = set()

    num_existing = 0
    num_new = 0
    num_expanded = 0
    num_uncertain = 0

    new_building_pixel_area = 0
    expanded_building_pixel_area = 0

    for a_det, a_m in a_masks:
        a_area = int(np.sum(a_m))
        a_centroid = a_det.get("centroid", [0, 0])

        best_iou = 0.0
        best_b_det = None
        best_overlap_ratio = 0.0
        best_b_mask = None
        min_centroid_dist = 9999.0

        for b_det, b_m in b_masks:
            inter = int(np.sum((a_m == 1) & (b_m == 1)))
            union = int(np.sum((a_m == 1) | (b_m == 1)))
            iou = inter / union if union > 0 else 0.0
            overlap_a = inter / a_area if a_area > 0 else 0.0

            b_centroid = b_det.get("centroid", [0, 0])
            dist = float(np.hypot(a_centroid[0] - b_centroid[0], a_centroid[1] - b_centroid[1]))

            if iou > best_iou:
                best_iou = iou
                best_b_det = b_det
                best_overlap_ratio = overlap_a
                best_b_mask = b_m
                min_centroid_dist = dist

        b_id = best_b_det["building_id"] if best_b_det else None
        b_conf = best_b_det["confidence"] if best_b_det else None
        b_area = best_b_det["pixel_area"] if best_b_det else 0

        # Classification decision tree (conservative)
        if best_iou >= iou_match_threshold:
            # Substantial spatial overlap with a known 2019 building
            if a_area > expansion_ratio_threshold * b_area and b_area > 0:
                status = "EXPANDED"
                num_expanded += 1
                matched_before_ids.add(b_id)
                # Change mask is the newly added footprint
                added_m = ((a_m == 1) & (best_b_mask == 0)).astype(np.uint8)
                change_px = int(np.sum(added_m))
                expanded_building_pixel_area += change_px
                change_mask[added_m == 1] = 255
            else:
                status = "EXISTING"
                num_existing += 1
                matched_before_ids.add(b_id)
                change_px = 0
        elif best_iou > 0.08 or (best_b_det is not None and best_overlap_ratio > 0.15):
            # Partial overlap — check if expansion or uncertain alignment
            if a_area > expansion_ratio_threshold * b_area:
                status = "EXPANDED"
                num_expanded += 1
                matched_before_ids.add(b_id)
                added_m = ((a_m == 1) & (best_b_mask == 0)).astype(np.uint8)
                change_px = int(np.sum(added_m))
                expanded_building_pixel_area += change_px
                change_mask[added_m == 1] = 255
            else:
                status = "UNCERTAIN"
                num_uncertain += 1
                change_px = 0
        else:
            # Little/no overlap (<0.08 IoU) with any 2019 detection
            # Check cumulative before mask overlap to guard against multi-building merging
            cum_overlap_px = int(np.sum((a_m == 1) & (cum_before_mask == 1)))
            if cum_overlap_px > 0.20 * a_area:
                status = "UNCERTAIN"
                num_uncertain += 1
                change_px = 0
            else:
                status = "NEW"
                num_new += 1
                change_px = a_area
                new_building_pixel_area += a_area
                change_mask[a_m == 1] = 255

        after_records.append({
            "building_id": a_det["building_id"],
            "status": status,
            "matched_before_id": b_id,
            "before_confidence": b_conf,
            "after_confidence": a_det["confidence"],
            "before_pixel_area": b_area if b_id else 0,
            "after_pixel_area": a_area,
            "change_pixel_area": change_px,
            "iou": round(float(best_iou), 4),
            "overlap_ratio": round(float(best_overlap_ratio), 4),
            "centroid_distance_px": round(float(min_centroid_dist), 2) if min_centroid_dist < 9000 else None,
            "bbox_xyxy": a_det["bbox_xyxy"],
            "centroid": a_centroid,
            "polygons": a_det["polygons"],
            "_mask": a_m
        })

    # 4. Check for BEFORE buildings that disappeared / were unmatched
    before_records = []
    for b_det, b_m in b_masks:
        b_id = b_det["building_id"]
        is_matched = b_id in matched_before_ids
        before_records.append({
            "building_id": b_id,
            "confidence": b_det["confidence"],
            "pixel_area": b_det["pixel_area"],
            "bbox_xyxy": b_det["bbox_xyxy"],
            "centroid": b_det.get("centroid", [0, 0]),
            "matched_in_after": is_matched,
            "polygons": b_det["polygons"],
            "_mask": b_m
        })

    total_change_pixel_area = new_building_pixel_area + expanded_building_pixel_area
    before_total_px = int(np.sum(cum_before_mask))
    after_total_px = int(np.sum(cum_after_mask))
    total_time_ms = round((time.perf_counter() - start_total_time) * 1000, 2)

    # 5. Generate Visualizations
    # Color palette for statuses (BGR format)
    COLOR_EXISTING = (60, 180, 75)    # Green
    COLOR_NEW = (40, 60, 235)         # Coral / Red
    COLOR_EXPANDED = (30, 140, 240)   # Orange / Amber
    COLOR_UNCERTAIN = (50, 215, 245)  # Yellow
    COLOR_BEFORE = (220, 160, 30)     # Blue/Cyan

    # Panel 1: Before Annotated
    p1_annotated = img_b.copy()
    p1_overlay = img_b.copy()
    for b_det in before_records:
        for poly in b_det["polygons"]:
            pts = np.array(poly, dtype=np.int32)
            cv2.fillPoly(p1_overlay, [pts], COLOR_BEFORE)
            cv2.polylines(p1_annotated, [pts], True, (255, 230, 100), 2)
        x1, y1, x2, y2 = [int(v) for v in b_det["bbox_xyxy"]]
        cv2.rectangle(p1_annotated, (x1, y1), (x2, y2), (255, 200, 50), 1)
        cv2.putText(p1_annotated, f"{b_det['building_id']} ({b_det['confidence']:.2f})", (x1, max(14, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
    p1_annotated = cv2.addWeighted(p1_overlay, 0.35, p1_annotated, 0.65, 0)

    # Panel 2: After Annotated
    p2_annotated = img_a.copy()
    p2_overlay = img_a.copy()
    for rec in after_records:
        status = rec["status"]
        color = COLOR_NEW if status == "NEW" else (COLOR_EXPANDED if status == "EXPANDED" else (COLOR_EXISTING if status == "EXISTING" else COLOR_UNCERTAIN))
        for poly in rec["polygons"]:
            pts = np.array(poly, dtype=np.int32)
            cv2.fillPoly(p2_overlay, [pts], color)
            cv2.polylines(p2_annotated, [pts], True, (255, 255, 255), 2)
        x1, y1, x2, y2 = [int(v) for v in rec["bbox_xyxy"]]
        cv2.rectangle(p2_annotated, (x1, y1), (x2, y2), color, 1)
        cv2.putText(p2_annotated, f"{rec['building_id']}: {status}", (x1, max(14, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1, cv2.LINE_AA)
    p2_annotated = cv2.addWeighted(p2_overlay, 0.40, p2_annotated, 0.60, 0)

    # Panel 3: Change Highlighting Only (NEW + EXPANDED on after image)
    p3_annotated = img_a.copy()
    p3_overlay = img_a.copy()
    p3_overlay[change_mask == 255] = COLOR_NEW
    p3_annotated = cv2.addWeighted(p3_overlay, 0.55, p3_annotated, 0.45, 0)

    # Draw crisp polygon outlines around new/expanded detections in Panel 3
    for rec in after_records:
        if rec["status"] in ("NEW", "EXPANDED"):
            for poly in rec["polygons"]:
                pts = np.array(poly, dtype=np.int32)
                cv2.polylines(p3_annotated, [pts], True, (255, 255, 255), 2)
            x1, y1, x2, y2 = [int(v) for v in rec["bbox_xyxy"]]
            cv2.putText(p3_annotated, f"{rec['building_id']} ({rec['status']})", (x1, max(14, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

    # Create composite 3-panel side-by-side banner
    banner_height = 42
    footer_height = 36
    panel_w, panel_h = w, h
    total_w = panel_w * 3
    total_h = panel_h + banner_height + footer_height

    canvas = np.zeros((total_h, total_w, 3), dtype=np.uint8)
    canvas[:] = (24, 26, 28)

    # Paste panels
    canvas[banner_height:banner_height + panel_h, 0:panel_w] = p1_annotated
    canvas[banner_height:banner_height + panel_h, panel_w:panel_w * 2] = p2_annotated
    canvas[banner_height:banner_height + panel_h, panel_w * 2:panel_w * 3] = p3_annotated

    # Vertical panel dividers
    cv2.line(canvas, (panel_w, 0), (panel_w, total_h), (60, 65, 70), 2)
    cv2.line(canvas, (panel_w * 2, 0), (panel_w * 2, total_h), (60, 65, 70), 2)

    # Header Titles
    cv2.putText(canvas, "1. BEFORE BASELINE (2019-01-31)", (20, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (220, 220, 220), 2, cv2.LINE_AA)
    cv2.putText(canvas, f"Buildings: {len(dets_before)} ({before_total_px} px)", (panel_w - 180, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1, cv2.LINE_AA)

    cv2.putText(canvas, "2. AFTER PROGRESSION (2025-01-30)", (panel_w + 20, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (220, 220, 220), 2, cv2.LINE_AA)
    cv2.putText(canvas, f"Buildings: {len(dets_after)} ({after_total_px} px)", (panel_w * 2 - 180, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1, cv2.LINE_AA)

    cv2.putText(canvas, "3. DETECTED FOOTPRINT CHANGE", (panel_w * 2 + 20, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (80, 120, 255), 2, cv2.LINE_AA)
    cv2.putText(canvas, f"New/Exp Area: {total_change_pixel_area} px", (panel_w * 3 - 210, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 200, 255), 1, cv2.LINE_AA)

    # Footer Metrics & Legend
    f_y = total_h - 12
    cv2.putText(canvas, f"YOLOv8s Building Segmentation (conf>={conf_threshold:.2f}) | MIHAN-042 (~500m x 500m)", (20, f_y), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (150, 150, 150), 1, cv2.LINE_AA)

    legend_text = f"Existing: {num_existing} (Green) | New: {num_new} (Red) | Expanded: {num_expanded} (Amber) | Uncertain: {num_uncertain} (Yellow)"
    cv2.putText(canvas, legend_text, (panel_w + 20, f_y), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (240, 240, 240), 1, cv2.LINE_AA)

    # 6. Save Artifacts
    saved_files = {}
    if output_dir:
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)

        p1_path = out_p / "before_annotated.jpg"
        p2_path = out_p / "after_annotated.jpg"
        mask_path = out_p / "change_mask.png"
        comp_path = out_p / "before_after_comparison.jpg"
        json_path = out_p / "results.json"

        cv2.imwrite(str(p1_path), p1_annotated)
        cv2.imwrite(str(p2_path), p2_annotated)
        cv2.imwrite(str(mask_path), change_mask)
        cv2.imwrite(str(comp_path), canvas)

        saved_files = {
            "before_annotated": str(p1_path),
            "after_annotated": str(p2_path),
            "change_mask": str(mask_path),
            "before_after_comparison": str(comp_path),
            "results_json": str(json_path)
        }

    # Clean internal non-serializable fields
    serializable_after = [{k: v for k, v in r.items() if not k.startswith("_")} for r in after_records]
    serializable_before = [{k: v for k, v in r.items() if not k.startswith("_")} for r in before_records]

    result_payload = {
        "status": "SUCCESS",
        "scope": "Building footprint change comparison (BEFORE vs AFTER)",
        "model": "keremberke/yolov8s-building-segmentation",
        "confidence_threshold": conf_threshold,
        "iou_match_threshold": iou_match_threshold,
        "total_inference_and_matching_time_ms": total_time_ms,
        "image_dimensions": {"width": w, "height": h, "channels": 3},
        "summary": {
            "total_before_detections": len(dets_before),
            "total_after_detections": len(dets_after),
            "num_existing": num_existing,
            "num_new": num_new,
            "num_expanded": num_expanded,
            "num_uncertain": num_uncertain,
            "before_building_pixel_area": before_total_px,
            "after_building_pixel_area": after_total_px,
            "new_building_pixel_area": new_building_pixel_area,
            "expanded_building_pixel_area": expanded_building_pixel_area,
            "total_change_pixel_area": total_change_pixel_area,
            "ground_area_m2": None,
            "geospatial_reliable": False,
            "geospatial_notes": "Current PNG crops do not retain embedded geotransform metadata. Ground area in m² is marked null."
        },
        "after_building_records": serializable_after,
        "before_building_records": serializable_before,
        "saved_files": saved_files
    }

    if output_dir:
        with open(out_p / "results.json", "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2)

    return result_payload


if __name__ == "__main__":
    import sys

    print("=" * 75)
    print("NAGPUR EARTHWATCH — YOLO BUILDING INTELLIGENCE ENGINE")
    print("=" * 75)

    # 1. Initialize Segmentor
    segmentor = BuildingSegmentor(conf_threshold=0.50)
    print(f"MODEL NAME : keremberke/yolov8s-building-segmentation")
    print(f"TASK       : {segmentor.task}")
    print(f"CLASSES    : {segmentor.names}")
    print(f"DEVICE     : {segmentor.device} ({segmentor.device_name})")

    # 2. Test Input Crops
    test_after = Path("backend/static/hotspot_crops/mihan-042/mihan-042_level1_after.png")
    test_before = Path("backend/static/hotspot_crops/mihan-042/mihan-042_level1_before.png")

    if not test_after.exists():
        print(f"Error: Input image not found: {test_after.resolve()}")
        sys.exit(1)

    print(f"INPUT IMAGE: {test_after.resolve()}")

    # 3. Run Inference on AFTER Image
    out_dir = Path("outputs/yolo_building_test")
    print(f"\nRunning YOLO inference on AFTER crop (conf>=0.50)...")
    res = segmentor.segment(test_after, conf_threshold=0.50, output_dir=out_dir)

    print(f"\nDETECTION RESULTS:")
    print(f"Number of Buildings Detected: {res['total_buildings_detected']}")
    print(f"Inference Time             : {res['inference_time_ms']:.2f} ms")
    print("-" * 75)
    for b in res["detections"]:
        cid = b["building_id"]
        conf = b["confidence"]
        bbox = [round(x, 1) for x in b["bbox_xyxy"]]
        area = b["pixel_area"]
        print(f"  * {cid:<9} | Confidence: {conf:.4f} ({conf*100:.1f}%) | Area: {area:>5} px | BBox: {bbox}")

    print("-" * 75)
    print(f"OUTPUT FILES:")
    for k, v in res.get("saved_files", {}).items():
        print(f"  - {k:<20}: {v}")

    # 4. Also verify BEFORE vs AFTER change comparison
    if test_before.exists():
        print(f"\nRunning BEFORE vs AFTER change comparison on MIHAN-042...")
        change_res = segmentor.compare(
            test_before,
            test_after,
            conf_threshold=0.50,
            output_dir="outputs/yolo_change_test"
        )
        s = change_res["summary"]
        print(f"Change Comparison Summary:")
        print(f"  - Before Buildings : {s['total_before_detections']}")
        print(f"  - After Buildings  : {s['total_after_detections']}")
        print(f"  - Existing Matched : {s['num_existing']}")
        print(f"  - NEW Buildings    : {s['num_new']}")
        print(f"  - Total Change Area: {s['total_change_pixel_area']} px")
        print(f"  - Output Dir       : outputs/yolo_change_test")

    print("=" * 75)

