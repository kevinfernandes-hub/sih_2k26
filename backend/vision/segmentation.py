"""
Spatial Change Segmentation & Geographic Polygon Extraction Engine
Nagpur EarthWatch — Sub-Meter Cadastral Parcel Geometry

Converts optical difference masks into precise WGS84 vector polygons,
calculates geodesic surface area in m², and produces cadastral boundary overlays.
"""

import math
from typing import Dict, List, Any, Optional, Tuple
import cv2
import numpy as np


def pixel_to_wgs84(
    px: float,
    py: float,
    img_w: int,
    img_h: int,
    bbox: List[float]
) -> Tuple[float, float]:
    """
    Converts pixel (x, y) to geographic WGS84 (lat, lng).
    bbox: [west, south, east, north]
    """
    west, south, east, north = bbox
    lng = west + (px / max(1, img_w)) * (east - west)
    lat = north - (py / max(1, img_h)) * (north - south)
    return round(lat, 6), round(lng, 6)


def calculate_polygon_area_m2(coords_lat_lng: List[List[float]]) -> float:
    """
    Calculates geographic polygon area in square meters using Shoelace formula
    with WGS84 latitude scaling.
    """
    if len(coords_lat_lng) < 3:
        return 0.0

    center_lat = sum(p[0] for p in coords_lat_lng) / len(coords_lat_lng)
    m_per_deg_lat = 111320.0
    m_per_deg_lng = 111320.0 * math.cos(math.radians(center_lat))

    # Convert coordinates to local metric offsets in meters
    xy_meters = []
    ref_lat, ref_lng = coords_lat_lng[0]
    for lat, lng in coords_lat_lng:
        y = (lat - ref_lat) * m_per_deg_lat
        x = (lng - ref_lng) * m_per_deg_lng
        xy_meters.append((x, y))

    # Shoelace formula for polygon area
    area = 0.0
    n = len(xy_meters)
    for i in range(n):
        j = (i + 1) % n
        area += xy_meters[i][0] * xy_meters[j][1]
        area -= xy_meters[j][0] * xy_meters[i][1]

    return round(abs(area) / 2.0, 1)


def segment_change_polygons(
    before_bgr: np.ndarray,
    after_bgr: np.ndarray,
    bbox_wgs84: List[float],
    threshold: int = 58,
    min_area_m2: float = 45.0,
    max_polygons: int = 12
) -> Dict[str, Any]:
    """
    Generates geographic change polygons and computed ground areas from aligned before/after images.
    """
    if before_bgr is None or after_bgr is None:
        return {
            "status": "UNAVAILABLE",
            "reason": "Missing imagery for segmentation.",
            "total_change_area_m2": 0.0,
            "polygons": []
        }

    h, w = after_bgr.shape[:2]

    # 1. Multi-channel optical differencing
    diff_b = cv2.absdiff(before_bgr[:, :, 0], after_bgr[:, :, 0])
    diff_g = cv2.absdiff(before_bgr[:, :, 1], after_bgr[:, :, 1])
    diff_r = cv2.absdiff(before_bgr[:, :, 2], after_bgr[:, :, 2])
    diff_rgb = cv2.max(cv2.max(diff_b, diff_g), diff_r)

    # 2. Scale-matched morphological calibration (7x7 kernel ~ 4.2m at 0.6m GSD)
    _, mask = cv2.threshold(diff_rgb, threshold, 255, cv2.THRESH_BINARY)
    kernel = np.ones((7, 7), np.uint8)
    mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_CLOSE, kernel)

    # 3. Contour extraction and geometric simplification
    contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    polygons = []
    total_area_m2 = 0.0

    for idx, cnt in enumerate(contours):
        if cv2.contourArea(cnt) < 15:
            continue

        # Approximate contour to smooth polygonal boundary
        epsilon = 0.015 * cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, epsilon, True)

        if len(approx) < 3:
            continue

        # Convert pixel points to WGS84 [lat, lng]
        coords = []
        for pt in approx:
            px, py = pt[0]
            lat, lng = pixel_to_wgs84(px, py, w, h, bbox_wgs84)
            coords.append([lat, lng])

        # Close the polygon ring
        if coords[0] != coords[-1]:
            coords.append(coords[0])

        area_m2 = calculate_polygon_area_m2(coords)
        if area_m2 < min_area_m2:
            continue

        # Centroid
        m = cv2.moments(cnt)
        if m["m00"] != 0:
            cx_px = m["m10"] / m["m00"]
            cy_px = m["m01"] / m["m00"]
            c_lat, c_lng = pixel_to_wgs84(cx_px, cy_px, w, h, bbox_wgs84)
        else:
            c_lat, c_lng = coords[0]

        total_area_m2 += area_m2
        polygons.append({
            "polygon_id": f"POLY-{idx + 1:02d}",
            "coordinates": coords,
            "area_m2": area_m2,
            "centroid": [c_lat, c_lng],
            "vertex_count": len(coords)
        })

    # Sort by largest changed area
    polygons.sort(key=lambda p: p["area_m2"], reverse=True)
    selected_polygons = polygons[:max_polygons]

    return {
        "status": "SUCCESS",
        "total_change_area_m2": round(total_area_m2, 1),
        "polygons_count": len(selected_polygons),
        "polygons": selected_polygons,
        "change_mask_pct": round((float(np.sum(mask_clean == 255)) / float(mask_clean.size)) * 100.0, 2)
    }
