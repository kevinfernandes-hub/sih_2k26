"""
Pipeline Orchestrator & Live Data Processing Service
Nagpur EarthWatch — Dual-Tier Urban Change Intelligence

Orchestrates multi-resolution spatial change detection:
- Tier 1: 10m Sentinel-2 multi-spectral differencing & SSIM structural divergence matrix
- Tier 2: ~0.6m Maxar Wayback historical imagery & scale-matched morphological calibration
- Extracts ranked candidate spatial hotspots for AI inspection
"""

import os
import re
import math
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from sentinelhub import (
    SHConfig,
    CRS,
    BBox,
    DataCollection,
    SentinelHubRequest,
    MimeType,
    SentinelHubCatalog
)

from backend.config import get_sh_config, RESULTS_DIR
from backend.hotspots import extract_hotspots_from_masks
from backend.wayback_live import fetch_live_wayback_tier

# True-color 2.5x gain evalscript for Sentinel-2 L2A
EVALSCRIPT_TRUE_COLOR = """
//VERSION=3
function setup() {
  return {
    input: [{ bands: ["B02", "B03", "B04"] }],
    output: { bands: 3 }
  };
}
function evaluatePixel(sample) {
  return [sample.B04 * 2.5, sample.B03 * 2.5, sample.B02 * 2.5];
}
"""

DATES_CACHE: Dict[str, List[Dict[str, Any]]] = {}


def build_bbox_from_point(lat: float, lng: float, padding: float = 0.024) -> BBox:
    """
    Builds a bounding box around (lat, lng) with padding (~5km span).
    """
    min_lng = lng - padding
    min_lat = lat - padding
    max_lng = lng + padding
    max_lat = lat + padding
    return BBox((min_lng, min_lat, max_lng, max_lat), crs=CRS.WGS84)


def get_available_scene_dates(
    bbox: BBox,
    start_date: str = "2020-01-01",
    end_date: str = "2025-03-01",
    config: Optional[SHConfig] = None
) -> List[Dict[str, Any]]:
    if config is None:
        config = get_sh_config()

    cache_key = f"{bbox.min_x:.4f}_{bbox.min_y:.4f}_{bbox.max_x:.4f}_{bbox.max_y:.4f}_{start_date}_{end_date}"
    if cache_key in DATES_CACHE:
        return DATES_CACHE[cache_key]

    catalog = SentinelHubCatalog(config=config)
    data_collection = DataCollection.SENTINEL2_L2A.define_from(
        name="s2l2a", service_url="https://sh.dataspace.copernicus.eu"
    )

    try:
        results = list(catalog.search(data_collection, bbox=bbox, time=(start_date, end_date)))
    except Exception as e:
        print(f"Catalog search error for available dates ({start_date} to {end_date}): {e}")
        return []

    date_map: Dict[str, Dict[str, Any]] = {}
    for r in results:
        p = r.get("properties", {})
        dt = p.get("datetime", "")
        if not dt or len(dt) < 10:
            continue
        date_str = dt[:10]
        cc = p.get("eo:cloud_cover", p.get("cloudCover", None))
        if cc is None:
            cc = 0.0
        cc_val = round(float(cc), 1)

        if date_str not in date_map or cc_val < date_map[date_str]["cloud_cover"]:
            date_map[date_str] = {
                "date": date_str,
                "cloud_cover": cc_val,
                "usable": cc_val < 15.0,
                "scene_id": r.get("id", "")
            }

    sorted_dates = sorted(date_map.values(), key=lambda x: x["date"])
    DATES_CACHE[cache_key] = sorted_dates
    return sorted_dates


def fetch_satellite_image(
    time_interval: Tuple[str, str],
    bbox: BBox,
    size: Tuple[int, int],
    config: SHConfig
) -> np.ndarray:
    """
    Fetches true-color Sentinel-2 image via Process API.
    """
    request = SentinelHubRequest(
        evalscript=EVALSCRIPT_TRUE_COLOR,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A.define_from(
                    name="s2l2a", service_url="https://sh.dataspace.copernicus.eu"
                ),
                time_interval=time_interval,
                other_args={"dataFilter": {"mosaickingOrder": "leastCC"}},
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.PNG)],
        bbox=bbox,
        size=size,
        config=config,
    )
    data = request.get_data()[0]
    return data


def normalize_contrast(img: np.ndarray) -> np.ndarray:
    return cv2.normalize(img, np.zeros_like(img), alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)


def compute_color_diff(
    before: np.ndarray,
    after: np.ndarray,
    threshold: int = 20,
    kernel_size: int = 3
) -> Tuple[float, np.ndarray, np.ndarray]:
    before_gray = cv2.cvtColor(before, cv2.COLOR_BGR2GRAY)
    after_gray = cv2.cvtColor(after, cv2.COLOR_BGR2GRAY)
    before_gray = normalize_contrast(before_gray)
    after_gray = normalize_contrast(after_gray)

    before_gray = cv2.GaussianBlur(before_gray, (5, 5), 0)
    after_gray = cv2.GaussianBlur(after_gray, (5, 5), 0)

    diff_b = cv2.absdiff(before[:, :, 0], after[:, :, 0])
    diff_g = cv2.absdiff(before[:, :, 1], after[:, :, 1])
    diff_r = cv2.absdiff(before[:, :, 2], after[:, :, 2])
    diff_rgb = cv2.max(cv2.max(diff_b, diff_g), diff_r)
    diff_gray = cv2.absdiff(before_gray, after_gray)
    diff = cv2.max(diff_rgb, diff_gray)

    _, change_mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    if kernel_size > 1:
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        change_mask = cv2.morphologyEx(change_mask, cv2.MORPH_OPEN, kernel)
        change_mask = cv2.morphologyEx(change_mask, cv2.MORPH_CLOSE, kernel)

    change_percent = (float(np.sum(change_mask == 255)) / float(change_mask.size)) * 100.0

    overlay = after.copy()
    overlay[change_mask == 255] = [30, 111, 201]  # Orange-red highlight in BGR
    blended = cv2.addWeighted(after, 0.65, overlay, 0.35, 0)

    return float(change_percent), change_mask, blended


def compute_ssim_diff(
    before: np.ndarray,
    after: np.ndarray,
    threshold: float = 0.55,
    kernel_size: int = 3
) -> Tuple[float, float, np.ndarray, np.ndarray]:
    score, diff_map = ssim(before, after, channel_axis=2, full=True)
    diff_map = np.mean(diff_map, axis=2)

    dissimilarity_map = ((1.0 - diff_map) * 255).astype(np.uint8)
    cutoff = int((1.0 - threshold) * 255)
    _, change_mask = cv2.threshold(dissimilarity_map, cutoff, 255, cv2.THRESH_BINARY)

    if kernel_size > 1:
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        change_mask = cv2.morphologyEx(change_mask, cv2.MORPH_OPEN, kernel)
        change_mask = cv2.morphologyEx(change_mask, cv2.MORPH_CLOSE, kernel)

    change_percent = (float(np.sum(change_mask == 255)) / float(change_mask.size)) * 100.0

    overlay = after.copy()
    overlay[change_mask == 255] = [30, 111, 201]
    blended = cv2.addWeighted(after, 0.65, overlay, 0.35, 0)

    return float(change_percent), float(score), change_mask, blended


def run_analysis_pipeline(
    lat: float,
    lng: float,
    location_name: str,
    before_date: Optional[str] = None,
    after_date: Optional[str] = None,
    base_url: str = "",
    size: Tuple[int, int] = (600, 500),
    local_before_path: Optional[str] = None,
    local_after_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes high-speed multi-tier spatial change detection across ANY searched location in Nagpur:
    - Concurrently downloads Sentinel-2 Before & After granules in parallel threads.
    - Concurrently fetches high-res Maxar Wayback tiles.
    - Extracts candidate hotspots and returns dual-tier intelligence in seconds.
    """
    config = get_sh_config()
    bbox = build_bbox_from_point(lat, lng, padding=0.024)
    bbox_list = [bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y]

    if before_date and after_date:
        before_date_str = before_date.strip()
        after_date_str = after_date.strip()
    else:
        # Verified clear dry-season scenes for Central India / Nagpur (Tile 44QMD)
        before_date_str = "2022-02-22"
        after_date_str = "2025-02-26"

    # Exact 1-day time intervals for instant satellite fetch
    before_interval = (f"{before_date_str}T00:00:00Z", f"{before_date_str}T23:59:59Z")
    after_interval = (f"{after_date_str}T00:00:00Z", f"{after_date_str}T23:59:59Z")

    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", location_name.lower())[:32]
    date_tag = f"{before_date_str.replace('-', '')}_{after_date_str.replace('-', '')}"
    loc_hash = hashlib.md5(f"{lat:.4f}_{lng:.4f}_{location_name}_{date_tag}".encode()).hexdigest()[:8]
    output_dir = RESULTS_DIR / f"{slug}_{date_tag}_{loc_hash}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Concurrently execute Sentinel-2 downloads and Wayback tile stitching
    local_before = Path(local_before_path) if local_before_path else None
    local_after = Path(local_after_path) if local_after_path else None
    use_local_pair = bool(local_before and local_after and local_before.is_file() and local_after.is_file())

    with ThreadPoolExecutor(max_workers=3) as executor:
        fut_wayback = executor.submit(
            fetch_live_wayback_tier,
            bbox=bbox_list,
            output_dir=output_dir,
            base_url=base_url,
            before_target="2019-01-31",
            after_target="2025-01-30",
            zoom=17
        )
        fut_before_s2 = None if use_local_pair else executor.submit(fetch_satellite_image, before_interval, bbox, size, config)
        fut_after_s2 = None if use_local_pair else executor.submit(fetch_satellite_image, after_interval, bbox, size, config)

        try:
            wayback_tier = fut_wayback.result(timeout=45)
        except Exception as e:
            print(f"Warning: Wayback tier fetch fallback: {e}")
            wayback_tier = None

        try:
            if use_local_pair:
                before_bgr = cv2.imread(str(local_before))
                after_bgr = cv2.imread(str(local_after))
                if before_bgr is None or after_bgr is None:
                    raise RuntimeError("Cached imagery could not be decoded")
                before_bgr = cv2.resize(before_bgr, size)
                after_bgr = cv2.resize(after_bgr, size)
            else:
                raw_before = fut_before_s2.result(timeout=25)
                raw_after = fut_after_s2.result(timeout=25)
                before_bgr = cv2.cvtColor(raw_before, cv2.COLOR_RGB2BGR)
                after_bgr = cv2.cvtColor(raw_after, cv2.COLOR_RGB2BGR)
        except Exception as e:
            if use_local_pair:
                raise RuntimeError(f"Cached Sentinel-2 imagery unavailable: {e}") from e
            print(f"Warning: Sentinel-2 Process API error ({e}), retrying synchronous fetch...")
            try:
                raw_before = fetch_satellite_image(before_interval, bbox, size, config)
                raw_after = fetch_satellite_image(after_interval, bbox, size, config)
                before_bgr = cv2.cvtColor(raw_before, cv2.COLOR_RGB2BGR)
                after_bgr = cv2.cvtColor(raw_after, cv2.COLOR_RGB2BGR)
            except Exception as e2:
                raise RuntimeError(f"Sentinel-2 imagery acquisition failed: {e2}") from e2

    # Run 10m change detection algorithms
    color_diff_pct, color_mask, color_overlay = compute_color_diff(
        before_bgr, after_bgr, threshold=20, kernel_size=3
    )
    ssim_pct, ssim_score, ssim_mask, ssim_overlay = compute_ssim_diff(
        before_bgr, after_bgr, threshold=0.55, kernel_size=3
    )

    before_path = output_dir / "before.png"
    after_path = output_dir / "after.png"
    color_overlay_path = output_dir / "color_overlay.png"
    ssim_overlay_path = output_dir / "ssim_overlay.png"

    cv2.imwrite(str(before_path), before_bgr)
    cv2.imwrite(str(after_path), after_bgr)
    cv2.imwrite(str(color_overlay_path), color_overlay)
    cv2.imwrite(str(ssim_overlay_path), ssim_overlay)

    # Sync into public directory for frontend instant access
    public_dir = Path(__file__).resolve().parent.parent / "public"
    public_results = public_dir / "results" / output_dir.name
    public_results.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(public_results / "before.png"), before_bgr)
    cv2.imwrite(str(public_results / "after.png"), after_bgr)
    cv2.imwrite(str(public_results / "color_overlay.png"), color_overlay)
    cv2.imwrite(str(public_results / "ssim_overlay.png"), ssim_overlay)

    # Extract candidate spatial hotspots from change masks
    extracted_hotspots = extract_hotspots_from_masks(
        color_mask=color_mask,
        ssim_mask=ssim_mask,
        bbox_wgs84=(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y),
        location_id=slug,
        min_area_px=20
    )

    if wayback_tier:
        for fname in ["wayback_before.png", "wayback_after.png", "wayback_color_overlay.png", "wayback_color_mask.png", "wayback_ssim_overlay.png"]:
            src_f = output_dir / fname
            if src_f.exists():
                dst_f = public_results / fname
                cv2.imwrite(str(dst_f), cv2.imread(str(src_f)))

    divergence = abs(color_diff_pct - ssim_pct)
    confidence = "high" if divergence <= 3.0 else "needs_review"
    rel_folder = f"/static/results/{output_dir.name}"

    if not wayback_tier:
        try:
            wayback_tier = fetch_live_wayback_tier(
                bbox=bbox_list,
                output_dir=output_dir,
                base_url=base_url,
                before_target="2019-01-31",
                after_target="2025-01-30",
                zoom=17
            )
            if wayback_tier:
                for fname in ["wayback_before.png", "wayback_after.png", "wayback_color_overlay.png", "wayback_color_mask.png", "wayback_ssim_overlay.png"]:
                    src_f = output_dir / fname
                    if src_f.exists():
                        dst_f = public_results / fname
                        cv2.imwrite(str(dst_f), cv2.imread(str(src_f)))
        except Exception as e:
            print(f"Synchronous fallback for Wayback tier failed: {e}")
            wayback_tier = None

    if not wayback_tier:
        wayback_tier = {
            "source": "ArcGIS World Imagery Wayback (~0.6m)",
            "available": False,
            "reason": "no_wayback_coverage",
            "note": "High-resolution imagery was not fetched for this AOI."
        }

    return {
        "location_name": location_name,
        "lat": lat,
        "lng": lng,
        "coords": f"{lng:.3f}° E, {lat:.3f}° N",
        "before_image_url": f"{base_url}{rel_folder}/before.png",
        "after_image_url": f"{base_url}{rel_folder}/after.png",
        "color_diff_overlay_url": f"{base_url}{rel_folder}/color_overlay.png",
        "ssim_overlay_url": f"{base_url}{rel_folder}/ssim_overlay.png",
        "color_diff_pct": round(color_diff_pct, 2),
        "ssim_pct": round(ssim_pct, 2),
        "ssim_score": round(ssim_score, 4),
        "confidence": confidence,
        "before_date": before_date_str,
        "after_date": after_date_str,
        "tiers": {
            "10m": {
                "source": "Sentinel-2 (Live Copernicus CDSE)",
                "beforeImage": f"{base_url}{rel_folder}/before.png",
                "afterImage": f"{base_url}{rel_folder}/after.png",
                "colorDiffOverlay": f"{base_url}{rel_folder}/color_overlay.png",
                "colorDiffPct": round(color_diff_pct, 2),
                "ssimOverlay": f"{base_url}{rel_folder}/ssim_overlay.png",
                "ssimPct": round(ssim_pct, 2),
                "ssimScore": round(ssim_score, 4)
            },
            "0.6m": wayback_tier
        },
        "hotspots": extracted_hotspots,
        "status": "success"
    }
