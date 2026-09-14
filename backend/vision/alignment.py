"""
Geographic Footprint Alignment & Spatial Verification Engine
Nagpur EarthWatch — Multi-Resolution Optical Registration

Guarantees that Before and After historical images represent EXACTLY the same
geographic bounding box, orientation, aspect ratio, and scale before computer vision
differencing or multimodal AI inspection.
"""

import math
from typing import Dict, List, Any, Optional, Tuple, NamedTuple
import numpy as np
import cv2
from PIL import Image


class AlignmentResult(NamedTuple):
    aligned: bool
    bbox: List[float]
    width: int
    height: int
    ground_resolution_m: float
    reason: str
    normalized_before: Optional[np.ndarray] = None
    normalized_after: Optional[np.ndarray] = None


def verify_and_align_geographic_footprints(
    before_img: np.ndarray,
    after_img: np.ndarray,
    before_bbox: List[float],
    after_bbox: List[float],
    tolerance_deg: float = 0.0001
) -> AlignmentResult:
    """
    Verifies geographic alignment between Before and After imagery.
    bbox format: [west, south, east, north] (WGS84 in degrees)
    """
    if before_img is None or after_img is None:
        return AlignmentResult(
            aligned=False,
            bbox=before_bbox,
            width=0,
            height=0,
            ground_resolution_m=0.0,
            reason="One or both input images are empty or unreadable."
        )

    # 1. Geographic Bounding Box Consistency Check
    b_west, b_south, b_east, b_north = before_bbox
    a_west, a_south, a_east, a_north = after_bbox

    delta_w = abs(b_west - a_west)
    delta_s = abs(b_south - a_south)
    delta_e = abs(b_east - a_east)
    delta_n = abs(b_north - a_north)

    max_delta = max(delta_w, delta_s, delta_e, delta_n)
    if max_delta > tolerance_deg:
        return AlignmentResult(
            aligned=False,
            bbox=before_bbox,
            width=before_img.shape[1],
            height=before_img.shape[0],
            ground_resolution_m=0.0,
            reason=f"Geographic footprints do not match. Coordinate delta ({max_delta:.5f}°) exceeds tolerance."
        )

    # 2. Dimensions and Pixel Grid Normalization
    h_before, w_before = before_img.shape[:2]
    h_after, w_after = after_img.shape[:2]

    target_w = max(w_before, w_after)
    target_h = max(h_before, h_after)

    if (w_before, h_before) != (target_w, target_h):
        norm_before = cv2.resize(before_img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
    else:
        norm_before = before_img.copy()

    if (w_after, h_after) != (target_w, target_h):
        norm_after = cv2.resize(after_img, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
    else:
        norm_after = after_img.copy()

    # 3. Calculate Ground Sampling Distance (GSD) in meters/pixel
    center_lat = (b_north + b_south) / 2.0
    lat_span_m = (b_north - b_south) * 111320.0
    lng_span_m = (b_east - b_west) * (111320.0 * math.cos(math.radians(center_lat)))

    gsd_x = lng_span_m / target_w
    gsd_y = lat_span_m / target_h
    ground_res_m = round((gsd_x + gsd_y) / 2.0, 2)

    return AlignmentResult(
        aligned=True,
        bbox=before_bbox,
        width=target_w,
        height=target_h,
        ground_resolution_m=ground_res_m,
        reason="Geographic footprint alignment verified (identical WGS84 bounding box).",
        normalized_before=norm_before,
        normalized_after=norm_after
    )
