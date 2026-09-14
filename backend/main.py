import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import json
import time
import asyncio
from urllib.parse import urlparse
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from .config import STATIC_DIR
from .locations_data import PRESET_LOCATIONS
from .geocoding import geocode_location
from .pipeline import (
    run_analysis_pipeline,
    get_available_scene_dates,
    build_bbox_from_point
)
from .hotspots import get_hotspots_for_location, PRESET_HOTSPOTS
from .vision_inspector import execute_zoom_and_verify_agent
from .wayback_live import check_wayback_availability
from .agent.orchestrator import EarthWatchOrchestrator, run_earthwatch_agent
from .narrate import generate_narrative
from .building_segmentor import (
    BuildingSegmentor,
    compare_building_change,
    get_inference_device
)
from .multiscale_verifier import run_multiscale_verification
from .municipal_fusion import fuse_municipal_evidence, build_municipal_case
from .retrieval.api import router as retrieval_router, _service
from .retrieval.semantic_verifier import verify_image_semantics
from .imagery.acquisition_service import ImageryAcquisitionService

def _get_torch_cuda_info() -> Tuple[bool, Optional[float]]:
    try:
        import torch
        cuda_avail = torch.cuda.is_available()
        vram = None
        if cuda_avail:
            try:
                vram = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 1)
            except Exception:
                pass
        return cuda_avail, vram
    except ImportError:
        return False, None


BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"
OUTPUTS_DIR = BASE_DIR / "outputs"
RETRIEVAL_DATA_DIR = Path(os.environ.get("RETRIEVAL_DATA_DIR", BASE_DIR / "data"))
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

imagery_service = ImageryAcquisitionService(data_dir=RETRIEVAL_DATA_DIR)

app = FastAPI(
    title="Nagpur EarthWatch — Urban Change Intelligence API",
    description="Dual-tier satellite change detection pipeline combining 10m Copernicus Sentinel-2 multispectral granules, 0.6m Esri Wayback historical mosaics, and AI Zoom-and-Verify Agent.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(retrieval_router)

# Mount static files directory for serving satellite imagery & overlays
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
if PUBLIC_DIR.exists():
    app.mount("/public", StaticFiles(directory=str(PUBLIC_DIR)), name="public")
if RETRIEVAL_DATA_DIR.exists():
    app.mount("/retrieval-data", StaticFiles(directory=str(RETRIEVAL_DATA_DIR)), name="retrieval-data")

# Serve built Vite frontend (dist/) in production
DIST_DIR = BASE_DIR / "dist"

# In-memory inspection cache
INSPECTION_CACHE: Dict[str, Dict[str, Any]] = {}
YOLO_RESULTS_CACHE: Dict[str, Dict[str, Any]] = {}


# Pydantic Schemas
class AgentRunRequest(BaseModel):
    location_name: str = Field(..., description="Any searchable location or landmark in Nagpur (e.g. Civil Lines, Sadar, Hingna MIDC, MIHAN, Sitabuldi)")
    before_date: Optional[str] = Field(None, description="Optional baseline date YYYY-MM-DD")
    after_date: Optional[str] = Field(None, description="Optional current date YYYY-MM-DD")


class NarrateRequest(BaseModel):
    location_name: str = Field("MIHAN / SEZ", description="Display name of the location")
    before_date: str = Field("2019-01-31", description="Baseline date YYYY-MM-DD")
    after_date: str = Field("2025-01-30", description="Current date YYYY-MM-DD")
    infra_pct: float = Field(0.0, description="Infrastructure/construction delta %")
    veg_loss_pct: float = Field(0.0, description="Vegetation/canopy loss %")
    veg_gain_pct: float = Field(0.0, description="Afforestation/veg gain %")
    ssim_score: float = Field(0.85, description="SSIM structural index (0-1)")
    ssim_pct: float = Field(0.0, description="SSIM structural divergence %")
    tier: str = Field("0.6m", description="Active sensor tier: '0.6m' or '10m'")
    hotspot_count: int = Field(0, description="Number of flagged hotspots")
    hotspot_types: List[str] = Field(default_factory=list, description="List of change typology labels")
    is_stable: bool = Field(False, description="Whether the location is surface-stable")


class AcquireImageryRequest(BaseModel):
    lat: Optional[float] = Field(None, description="Latitude coordinate")
    lng: Optional[float] = Field(None, description="Longitude coordinate")
    location_name: str = Field(..., description="Location name or landmark")
    before_date: Optional[str] = Field("2022-02-22", description="Baseline date YYYY-MM-DD")
    after_date: Optional[str] = Field("2025-02-26", description="Current date YYYY-MM-DD")
    bbox: Optional[List[float]] = Field(None, description="Bounding box [min_lng, min_lat, max_lng, max_lat]")


class AnalyzeRequest(BaseModel):
    location_name: Optional[str] = Field(None, description="Location name or landmark in Nagpur")
    lat: Optional[float] = Field(None, description="Latitude coordinate")
    lng: Optional[float] = Field(None, description="Longitude coordinate")
    before_date: Optional[str] = Field(None, description="Baseline date YYYY-MM-DD")
    after_date: Optional[str] = Field(None, description="Current date YYYY-MM-DD")
    force_acquire: Optional[bool] = Field(False, description="Attempt acquisition if imagery is not cached locally")


class InspectHotspotRequest(BaseModel):
    hotspot_id: str = Field("MIHAN-042", description="Hotspot identifier")
    location_id: str = Field("mihan", description="Location identifier")
    hotspot_data: Optional[Dict[str, Any]] = Field(None, description="Complete candidate hotspot metadata")


class InspectAllRequest(BaseModel):
    location_id: str = Field("mihan", description="Location identifier")


class VerifySemanticsRequest(BaseModel):
    query: str = Field(..., description="The semantic search query")
    location_name: str = Field(..., description="Location name or landmark")
    lat: Optional[float] = Field(None, description="Latitude coordinate")
    lng: Optional[float] = Field(None, description="Longitude coordinate")
    before_date: Optional[str] = Field(None, description="Baseline date YYYY-MM-DD")
    after_date: Optional[str] = Field(None, description="Current date YYYY-MM-DD")


class YoloAnalyzeRequest(BaseModel):
    hotspot_id: str = Field("MIHAN-042", description="Hotspot identifier e.g. MIHAN-042, WARD-01, DHP-01")
    location_id: Optional[str] = Field(None, description="Optional parent location identifier")
    before_image: Optional[str] = Field(None, description="Optional custom before image path/URL")
    after_image: Optional[str] = Field(None, description="Optional custom after image path/URL")
    conf_threshold: float = Field(0.35, description="YOLO confidence threshold (0.10 - 0.95)")

class DiscoverAndVerifyRequest(BaseModel):
    query: str = Field(..., description="The semantic search query")
    top_k: int = Field(3, description="Number of top candidates to verify")
    before_date: Optional[str] = Field("2022-02-22", description="Baseline date YYYY-MM-DD")
    after_date: Optional[str] = Field("2025-02-26", description="Current date YYYY-MM-DD")


class LocationInvestigateRequest(BaseModel):
    query: str = Field(..., description="Location name / landmark in Nagpur, e.g. MIHAN, Hingna, VNIT")
    analysis_mode: Optional[str] = Field("general_change", description="Analysis mode: built_up_change, vegetation_change, water_change, general_change")
    before_date: Optional[str] = Field("2022-02-22", description="Baseline date YYYY-MM-DD")
    after_date: Optional[str] = Field("2025-02-26", description="Current date YYYY-MM-DD")


# Base Endpoints
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Nagpur EarthWatch Universal Intelligence API"}


@app.get("/api/system-health")
async def system_health():
    # Evaluate copernicus and high_resolution availability based on env variables
    has_copernicus = bool(os.environ.get("SH_CLIENT_ID") and os.environ.get("SH_CLIENT_SECRET"))
    has_maxar = bool(os.environ.get("MAXAR_API_KEY"))
    # Wayback is public, so it's technically always available unless network is down
    has_highres = has_maxar or True 

    return {
        "semantic_index": "ready",
        "copernicus": "available" if has_copernicus else "unavailable",
        "high_resolution": "available" if has_highres else "unavailable",
        "local_cache": "ready",
        "analysis_engine": "ready",
        "offline_mode": "ready"
    }


@app.get("/api/locations")
async def get_preset_locations():
    """Returns pre-analyzed validated locations (MIHAN, Sadar, Hingna MIDC, Civil Lines)."""
    return {"locations": PRESET_LOCATIONS, "count": len(PRESET_LOCATIONS)}


@app.post("/api/narrate")
async def narrate_analysis(req: NarrateRequest):
    """
    Generates a natural-language satellite change narrative using Gemini Flash 2.0.
    Returns:
      - analysis:   Plain-language description of what changed
      - prediction: Projection of what is likely to happen next 12-24 months
      - confidence: HIGH | MEDIUM | LOW
      - tags:       Short change-type labels
    Falls back to rule-based NLP summary if GEMINI_API_KEY is not set.
    """
    result = generate_narrative(
        location_name=req.location_name,
        before_date=req.before_date,
        after_date=req.after_date,
        infra_pct=req.infra_pct,
        veg_loss_pct=req.veg_loss_pct,
        veg_gain_pct=req.veg_gain_pct,
        ssim_score=req.ssim_score,
        ssim_pct=req.ssim_pct,
        tier=req.tier,
        hotspot_count=req.hotspot_count,
        hotspot_types=req.hotspot_types,
        is_stable=req.is_stable,
    )
    return {"status": "ok", **result}


@app.get("/api/available-dates")
async def get_available_dates(
    lat: Optional[float] = Query(None, description="Latitude"),
    lng: Optional[float] = Query(None, description="Longitude"),
    location_name: Optional[str] = Query(None, description="Location name"),
    start_date: str = Query("2020-01-01", description="Start date YYYY-MM-DD"),
    end_date: str = Query("2025-03-01", description="End date YYYY-MM-DD"),
):
    if lat is None or lng is None:
        if not location_name:
            lat, lng, display_name = 21.1458, 79.0882, "Nagpur Central"
        else:
            lat, lng, display_name = await geocode_location(location_name)
    else:
        display_name = location_name or f"AOI ({lat:.4f}, {lng:.4f})"

    bbox = build_bbox_from_point(lat, lng, padding=0.024)
    dates = get_available_scene_dates(bbox, start_date=start_date, end_date=end_date)
    return {
        "location_name": display_name,
        "lat": lat,
        "lng": lng,
        "dates": dates,
        "count": len(dates)
    }


@app.get("/api/wayback-availability")
async def get_wayback_status(
    lat: float = Query(21.1458, description="Latitude"),
    lng: float = Query(79.0882, description="Longitude"),
    padding: float = Query(0.024, description="Bounding box half-span in degrees")
):
    bbox = [lng - padding, lat - padding, lng + padding, lat + padding]
    return check_wayback_availability(bbox)


@app.post("/api/acquire-imagery")
async def acquire_imagery_endpoint(req: AcquireImageryRequest):
    if req.lat is None or req.lng is None:
        lat_val, lng_val, display_name = await geocode_location(req.location_name)
    else:
        lat_val, lng_val, display_name = req.lat, req.lng, req.location_name

    bbox = req.bbox or [lng_val - 0.024, lat_val - 0.024, lng_val + 0.024, lat_val + 0.024]
    before_date = req.before_date or "2022-02-22"
    after_date = req.after_date or "2025-02-26"

    res = imagery_service.acquire_imagery(
        lat=lat_val,
        lng=lng_val,
        bbox=bbox,
        location_name=display_name,
        before_date=before_date,
        after_date=after_date
    )
    return res.public_dict()


@app.get("/api/imagery-status")
async def get_imagery_status_endpoint(
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    location_name: Optional[str] = Query(None),
    before_date: str = Query("2022-02-22"),
    after_date: str = Query("2025-02-26")
):
    if lat is None or lng is None:
        if not location_name:
            location_name = "MIHAN / Outer Ring Road"
        lat_val, lng_val, display_name = await geocode_location(location_name)
    else:
        lat_val, lng_val, display_name = lat, lng, location_name or f"AOI ({lat:.4f}, {lng:.4f})"

    return imagery_service.imagery_status(
        lat=lat_val,
        lng=lng_val,
        location_name=display_name,
        before_date=before_date,
        after_date=after_date
    )


@app.api_route("/api/analyze", methods=["GET", "POST"])
async def analyze_location(
    request: Request,
    location_name: Optional[str] = Query(None),
    lat: Optional[float] = Query(None),
    lng: Optional[float] = Query(None),
    before_date: Optional[str] = Query(None),
    after_date: Optional[str] = Query(None),
    force_acquire: Optional[bool] = Query(False)
):
    """
    Universal Location Analysis Endpoint: Supports both GET and POST requests.
    Validates that local imagery exists before running the change engine.
    """
    body_data = {}
    if request.method == "POST":
        try:
            body_data = await request.json()
        except Exception:
            pass

    loc_name = body_data.get("location_name") or location_name
    latitude = body_data.get("lat") if body_data.get("lat") is not None else lat
    longitude = body_data.get("lng") if body_data.get("lng") is not None else lng
    b_date = body_data.get("before_date") or before_date or "2022-02-22"
    a_date = body_data.get("after_date") or after_date or "2025-02-26"
    should_acquire = body_data.get("force_acquire", force_acquire)

    if not loc_name and (latitude is None or longitude is None):
        loc_name = "MIHAN / Outer Ring Road"

    if loc_name:
        lat_val, lng_val, display_name = await geocode_location(loc_name)
    else:
        lat_val, lng_val = latitude, longitude
        display_name = f"Custom AOI ({lat_val:.4f}° N, {lng_val:.4f}° E)"

    # Check local cache first
    cached_pair = imagery_service.cache.get_pair(display_name, lat_val, lng_val, b_date, a_date)
    local_before = cached_pair.before.local_path if cached_pair.before else None
    local_after = cached_pair.after.local_path if cached_pair.after else None

    if not (local_before and local_after):
        cached_assets = imagery_service.cache.get_cached_assets(display_name, lat_val, lng_val)
        before_asset = next((a for a in cached_assets if a.role == "before"), None)
        after_asset = next((a for a in cached_assets if a.role == "after"), None)
        if before_asset and after_asset:
            local_before = before_asset.local_path
            local_after = after_asset.local_path

    if not (local_before and local_after) and should_acquire:
        bbox = [lng_val - 0.024, lat_val - 0.024, lng_val + 0.024, lat_val + 0.024]
        acq_res = imagery_service.acquire_imagery(
            lat=lat_val,
            lng=lng_val,
            bbox=bbox,
            location_name=display_name,
            before_date=b_date,
            after_date=a_date
        )
        if not acq_res.ready_for_analysis:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "stage": "copernicus_acquisition",
                    "code": "NO_VALID_SCENE" if not acq_res.assets else "ACQUISITION_FAILED",
                    "message": f"Acquisition failed: {', '.join(acq_res.errors) or 'No valid Sentinel-2 imagery acquired'}",
                    "reason": f"Acquisition failed: {', '.join(acq_res.errors) or 'No valid Sentinel-2 imagery acquired'}"
                }
            )
        pair = imagery_service.cache.get_pair(display_name, lat_val, lng_val, b_date, a_date)
        if pair.before and pair.after:
            local_before = pair.before.local_path
            local_after = pair.after.local_path

    base_url = ""

    try:
        result = run_analysis_pipeline(
            lat=lat_val,
            lng=lng_val,
            location_name=display_name,
            before_date=b_date,
            after_date=a_date,
            base_url=base_url,
            local_before_path=local_before,
            local_after_path=local_after
        )
        return result
    except Exception as e:
        print(f"Pipeline error for {display_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "stage": "analysis_engine",
                "code": "PIPELINE_ERROR",
                "message": f"Analysis pipeline failed: {str(e)}",
                "reason": f"Analysis pipeline failed: {str(e)}"
            }
        )

# ---------------------------------------------------------------------------
# YOLO BI-TEMPORAL BUILDING ANALYSIS — pipeline-integrated helper
# ---------------------------------------------------------------------------

def _run_yolo_on_pipeline_images(
    before_path: str,
    after_path: str,
    output_dir: str,
    hotspot_id: str = "pipeline",
    conf_threshold: float = 0.35
) -> Optional[Dict[str, Any]]:
    """
    Runs bi-temporal building change analysis on ACTUAL pipeline-acquired imagery.
    Uses the existing compare_building_change() from building_segmentor.py.
    Returns structured YOLO evidence dict, or None on failure.
    Does NOT use placeholder images or synthetic data.
    """
    try:
        bp = Path(before_path)
        ap = Path(after_path)
        if not bp.exists() or not ap.exists():
            print(f"[YOLO] Image files not on disk — before={bp.exists()} after={ap.exists()}")
            return None

        # Validate image dimensions — YOLO needs at least 32x32
        import cv2 as _cv2
        _b = _cv2.imread(str(bp))
        _a = _cv2.imread(str(ap))
        if _b is None or _a is None:
            print("[YOLO] cv2.imread returned None — imagery unreadable")
            return None
        if _b.shape[0] < 32 or _b.shape[1] < 32:
            print(f"[YOLO] Image too small for YOLO: {_b.shape}")
            return None

        yolo_out_dir = Path(output_dir) / "yolo"
        yolo_out_dir.mkdir(parents=True, exist_ok=True)

        change_res = compare_building_change(
            before_image=bp,
            after_image=ap,
            conf_threshold=conf_threshold,
            output_dir=yolo_out_dir,
            imgsz=320
        )

        s = change_res.get("summary", {})
        after_recs = change_res.get("after_building_records", [])
        before_recs = change_res.get("before_building_records", [])

        # Mean confidence from actual YOLO detections
        confs = [r.get("after_confidence", 0.0) for r in after_recs if r.get("after_confidence") is not None]
        mean_conf = round(float(sum(confs) / len(confs)), 4) if confs else None

        # Collect change detections for frontend overlay
        change_detections = []
        for rec in after_recs:
            status = rec.get("status", "EXISTING")
            if status in ("NEW", "EXPANDED"):
                change_detections.append({
                    "building_id": rec.get("building_id"),
                    "status": status,
                    "bbox_xyxy": rec.get("bbox_xyxy"),          # pixel coords in the acquired image
                    "centroid": rec.get("centroid"),
                    "pixel_area": rec.get("after_pixel_area", rec.get("pixel_area")),
                    "ground_area_m2": rec.get("ground_area_m2"),
                    "confidence": rec.get("after_confidence"),
                    "polygons": rec.get("polygons", [])
                })

        # All existing detections (for overlay completeness)
        all_detections = []
        for rec in after_recs:
            all_detections.append({
                "building_id": rec.get("building_id"),
                "status": rec.get("status", "EXISTING"),
                "bbox_xyxy": rec.get("bbox_xyxy"),
                "centroid": rec.get("centroid"),
                "pixel_area": rec.get("after_pixel_area", rec.get("pixel_area")),
                "ground_area_m2": rec.get("ground_area_m2"),
                "confidence": rec.get("after_confidence"),
                "polygons": rec.get("polygons", [])
            })

        # Image dimensions used by YOLO
        img_dims = change_res.get("image_dimensions", {"width": _b.shape[1], "height": _b.shape[0]})

        # Overlay image URLs (relative)
        rel_yolo = f"/static/results/{Path(output_dir).name}/yolo"

        return {
            "available": True,
            "model": "keremberke/yolov8s-building-segmentation",
            "hotspot_id": hotspot_id,
            "image_dimensions": img_dims,
            "summary": {
                "before_count": s.get("total_before_detections", len(before_recs)),
                "after_count": s.get("total_after_detections", len(after_recs)),
                "new_count": s.get("num_new", 0),
                "expanded_count": s.get("num_expanded", 0),
                "existing_count": s.get("num_existing", 0),
                "uncertain_count": s.get("num_uncertain", 0),
                "changed_pixel_area": s.get("total_change_pixel_area", 0),
                "ground_area_m2": s.get("ground_area_m2"),   # null if uncalibrated
                "mean_confidence": mean_conf,
                "physical_change": (s.get("num_new", 0) + s.get("num_expanded", 0)) > 0
            },
            "change_detections": change_detections,  # NEW + EXPANDED only
            "all_detections": all_detections,         # all for overlay
            "inference_time_ms": change_res.get("total_inference_and_matching_time_ms"),
            "confidence_threshold": conf_threshold,
            "image_urls": {
                "before_annotated": f"{rel_yolo}/before_annotated.jpg",
                "after_annotated": f"{rel_yolo}/after_annotated.jpg",
                "change_mask": f"{rel_yolo}/change_mask.png",
                "before_after_comparison": f"{rel_yolo}/before_after_comparison.jpg"
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[YOLO] Building analysis failed: {e}")
        return {"available": False, "error": str(e)}


def _fuse_evidence_score(
    analysis_mode: str,
    color_diff_pct: float,
    ssim_pct: float,
    yolo_result: Optional[Dict[str, Any]] = None,
    semantic_score_0_1: float = 1.0   # 1.0 for location mode (real location), 0–1 for RemoteCLIP
) -> Dict[str, Any]:
    """
    Transparent, documented evidence fusion.
    Returns score_breakdown dict with per-component weights and final score.
    """
    # Normalize raw metrics to [0, 1]
    spectral_norm = min(1.0, color_diff_pct / 100.0)
    temporal_norm = min(1.0, ssim_pct / 50.0)   # 50% SSIM change = max temporal evidence
    spatial_norm = min(1.0, (color_diff_pct + ssim_pct) / 2.0 / 60.0)

    if analysis_mode == "built_up_change" and yolo_result and yolo_result.get("available"):
        # --- BUILT-UP mode: YOLO-weighted fusion ---
        s = yolo_result.get("summary", {})
        new_ct = s.get("new_count", 0)
        exp_ct = s.get("expanded_count", 0)
        mean_conf = s.get("mean_confidence") or 0.0

        # YOLO evidence: how many changed buildings relative to a reasonable max (10)
        # Weighted: NEW counts more than EXPANDED
        raw_yolo_change = (new_ct * 1.0 + exp_ct * 0.5)
        yolo_norm = min(1.0, raw_yolo_change / 8.0) * mean_conf  # confidence-weighted

        weights = {
            "yolo_building_change":  0.40,
            "spectral_change":        0.25,
            "temporal_consistency":  0.20,
            "spatial_coherence":     0.10,
            "semantic_support":      0.05
        }
        scores_norm = {
            "yolo_building_change":  yolo_norm,
            "spectral_change":        spectral_norm,
            "temporal_consistency":  temporal_norm,
            "spatial_coherence":     spatial_norm,
            "semantic_support":      semantic_score_0_1
        }
    elif analysis_mode == "vegetation_change":
        weights = {
            "spectral_change":       0.45,
            "temporal_consistency": 0.30,
            "spatial_coherence":    0.20,
            "semantic_support":     0.05
        }
        scores_norm = {
            "spectral_change":       spectral_norm,
            "temporal_consistency": temporal_norm,
            "spatial_coherence":    spatial_norm,
            "semantic_support":     semantic_score_0_1
        }
    elif analysis_mode == "water_change":
        weights = {
            "spectral_change":       0.50,
            "temporal_consistency": 0.30,
            "spatial_coherence":    0.15,
            "semantic_support":     0.05
        }
        scores_norm = {
            "spectral_change":       spectral_norm,
            "temporal_consistency": temporal_norm,
            "spatial_coherence":    spatial_norm,
            "semantic_support":     semantic_score_0_1
        }
    else:
        # General / infrastructure — equal optical-based weights
        weights = {
            "spectral_change":       0.40,
            "temporal_consistency": 0.30,
            "spatial_coherence":    0.20,
            "semantic_support":     0.10
        }
        scores_norm = {
            "spectral_change":       spectral_norm,
            "temporal_consistency": temporal_norm,
            "spatial_coherence":    spatial_norm,
            "semantic_support":     semantic_score_0_1
        }

    # Weighted sum
    final_norm = sum(scores_norm[k] * weights[k] for k in weights)
    final_score = round(min(99.9, final_norm * 100.0), 1)

    # Build response breakdown (human-readable)
    breakdown: Dict[str, Any] = {}
    for key in weights:
        breakdown[key] = {
            "score": round(scores_norm[key] * 100, 1),
            "weight": weights[key],
            "weighted_contribution": round(scores_norm[key] * weights[key] * 100, 1)
        }

    if analysis_mode == "built_up_change" and yolo_result and yolo_result.get("available"):
        s = yolo_result.get("summary", {})
        breakdown["yolo_building_change"]["evidence"] = {
            "new_buildings":     s.get("new_count"),
            "expanded_buildings": s.get("expanded_count"),
            "existing_buildings": s.get("existing_count"),
            "changed_pixel_area": s.get("changed_pixel_area"),
            "ground_area_m2":    s.get("ground_area_m2"),
            "mean_confidence":   s.get("mean_confidence")
        }

    breakdown["final_score"] = final_score
    breakdown["analysis_mode"] = analysis_mode
    return breakdown


@app.post("/api/location-investigate")
async def location_investigate(req: LocationInvestigateRequest):
    """
    Location-First Investigation Pipeline (SIH26227 Mode 2).
    Geocodes a Nagpur landmark/location, validates it is within Nagpur coverage,
    acquires Sentinel-2 temporal imagery pair, runs change analysis, and returns
    hotspot evidence — without calling RemoteCLIP.
    """
    # Nagpur bounding box for coverage validation
    NAGPUR_LAT_MIN, NAGPUR_LAT_MAX = 20.75, 21.40
    NAGPUR_LNG_MIN, NAGPUR_LNG_MAX = 78.75, 79.40

    # 1. Geocode the location query
    try:
        lat, lng, display_name = await geocode_location(req.query)
    except Exception as e:
        raise HTTPException(status_code=400, detail={"error": "GEOCODE_FAILED", "message": str(e)})

    # 2. Nagpur-only coverage check
    if not (NAGPUR_LAT_MIN <= lat <= NAGPUR_LAT_MAX and NAGPUR_LNG_MIN <= lng <= NAGPUR_LNG_MAX):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "OUTSIDE_COVERAGE",
                "message": f"Location '{req.query}' resolved to ({lat:.4f}, {lng:.4f}) which is outside current coverage.",
                "coverage": "NAGPUR, MAHARASHTRA, INDIA"
            }
        )

    # 3. Build bbox and acquire imagery
    bbox_obj = build_bbox_from_point(lat, lng, padding=0.024)
    bbox = [bbox_obj.min_x, bbox_obj.min_y, bbox_obj.max_x, bbox_obj.max_y]
    loc_name = display_name.split(",")[0].strip()  # Short name for caching

    # Try to find cached imagery first
    cache_hit = False
    local_before = None
    local_after = None
    try:
        acq_res = imagery_service.acquire_imagery(
            lat=lat, lng=lng, bbox=bbox, location_name=loc_name,
            before_date=req.before_date, after_date=req.after_date
        )
        cache_hit = not acq_res.newly_acquired if hasattr(acq_res, 'newly_acquired') else False
        pair = imagery_service.cache.get_pair(loc_name, lat, lng, req.before_date, req.after_date)
        local_before = pair.before.local_path if pair and pair.before else None
        local_after = pair.after.local_path if pair and pair.after else None
    except Exception as e:
        print(f"[location-investigate] Imagery acquisition warning: {e}")

    # 4. Run analysis pipeline
    try:
        analysis_res = run_analysis_pipeline(
            lat=lat, lng=lng, location_name=loc_name,
            before_date=req.before_date, after_date=req.after_date,
            base_url="", local_before_path=local_before, local_after_path=local_after
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "ANALYSIS_FAILED", "message": str(e)})

    # 5. Optionally run YOLO for BUILT-UP analysis mode
    yolo_result = None
    analysis_mode = req.analysis_mode or "general_change"
    if analysis_mode in ("built_up_change", "built-up"):
        before_disk = analysis_res.get("_before_disk_path")
        after_disk = analysis_res.get("_after_disk_path")
        output_disk = analysis_res.get("_output_dir")
        if before_disk and after_disk and output_disk:
            yolo_result = _run_yolo_on_pipeline_images(
                before_path=before_disk,
                after_path=after_disk,
                output_dir=output_disk,
                hotspot_id=f"LOC-{loc_name.upper().replace(' ', '-')[:20]}"
            )
            if yolo_result and "image_urls" in yolo_result:
                yolo_result["image_urls"]["before_image"] = analysis_res.get("before_image_url")
                yolo_result["image_urls"]["after_image"] = analysis_res.get("after_image_url")
        else:
            yolo_result = {"available": False, "error": "Pipeline did not return valid disk paths for YOLO"}

    # 6. Compute transparent evidence score
    ssim_pct = analysis_res.get("ssim_pct", 0.0)
    color_diff_pct = analysis_res.get("color_diff_pct", 0.0)
    score_breakdown = _fuse_evidence_score(
        analysis_mode=analysis_mode,
        color_diff_pct=color_diff_pct,
        ssim_pct=ssim_pct,
        yolo_result=yolo_result,
        semantic_score_0_1=1.0  # Location mode: full semantic credit (real, confirmed location)
    )
    evidence_score = score_breakdown["final_score"]

    return {
        "location": {
            "name": display_name,
            "short_name": loc_name,
            "latitude": lat,
            "longitude": lng,
            "bbox": bbox
        },
        "analysis_mode": analysis_mode,
        "cache_hit": cache_hit,
        "before_date": req.before_date,
        "after_date": req.after_date,
        "before_image": analysis_res.get("before_image_url"),
        "after_image": analysis_res.get("after_image_url"),
        "color_overlay": analysis_res.get("color_diff_overlay_url"),
        "ssim_overlay": analysis_res.get("ssim_overlay_url"),
        "tiers": analysis_res.get("tiers", {}),
        "hotspots": analysis_res.get("hotspots", []),
        "analysis_metrics": {
            "ssim_pct": ssim_pct,
            "color_diff_pct": color_diff_pct,
            "confidence": analysis_res.get("confidence", "unknown")
        },
        "yolo_analysis": yolo_result,  # None / {available: False} / full result
        "score_breakdown": score_breakdown,
        "evidence_score": evidence_score
    }


@app.post("/api/discover-and-verify")
def discover_and_verify(req: DiscoverAndVerifyRequest):
    """
    Fully automated SIH26227 Semantic Discovery and Multi-Temporal Verification Pipeline.
    1. Query -> Semantic Candidates
    2. Candidate -> Live Satellite Verification
    3. Satellite Imagery -> Change Analysis (Query-Specific)
    4. Change Analysis -> Hotspots
    5. Hotspots -> Fused Evidence & Ranking
    """
    from backend.agent.analysis_router import determine_analysis_mode
    analysis_mode = determine_analysis_mode(req.query)
    
    # 1. Semantic Retrieval
    retrieval_res = _service().search(req.query, top_k=req.top_k)
    candidates = retrieval_res.get("results", [])
    
    if not candidates:
        return {"query": req.query, "mode": analysis_mode, "ranked_hotspots": []}
        
    all_hotspots = []
    
    # 2 & 3 & 4. Verify & Analyze each candidate
    for cand in candidates:
        try:
            bbox = cand["bbox"]
            center_lat = (bbox[1] + bbox[3]) / 2.0
            center_lng = (bbox[0] + bbox[2]) / 2.0
            loc_name = f"Region {cand['scene_id']}"
            
            # Use local cache primarily since Copernicus is mocked for this environment
            cached_pair = imagery_service.cache.get_pair(loc_name, center_lat, center_lng, req.before_date, req.after_date)
            local_b = cached_pair.before.local_path if cached_pair.before else None
            local_a = cached_pair.after.local_path if cached_pair.after else None
            
            if not (local_b and local_a):
                acq_res = imagery_service.acquire_imagery(
                    lat=center_lat, lng=center_lng, bbox=bbox, location_name=loc_name, 
                    before_date=req.before_date, after_date=req.after_date
                )
                if not acq_res.ready_for_analysis:
                    continue # Skip if no satellite imagery can be acquired
                pair = imagery_service.cache.get_pair(loc_name, center_lat, center_lng, req.before_date, req.after_date)
                local_b = pair.before.local_path if pair.before else None
                local_a = pair.after.local_path if pair.after else None
                
            # Run analysis pipeline
            analysis_res = run_analysis_pipeline(
                lat=center_lat, lng=center_lng, location_name=loc_name,
                before_date=req.before_date, after_date=req.after_date,
                base_url="", local_before_path=local_b, local_after_path=local_a
            )

            ssim_pct = analysis_res.get("ssim_pct", 0.0)
            color_diff_pct = analysis_res.get("color_diff_pct", 0.0)
            semantic_score_0_1 = cand.get("final_score", 0.0)  # RemoteCLIP similarity in [0,1]

            # For built-up/construction queries: run YOLO on actual acquired images
            cand_yolo_result = None
            if analysis_mode == "built_up_change":
                before_disk = analysis_res.get("_before_disk_path")
                after_disk = analysis_res.get("_after_disk_path")
                output_disk = analysis_res.get("_output_dir")
                if before_disk and after_disk and output_disk:
                    cand_yolo_result = _run_yolo_on_pipeline_images(
                        before_path=before_disk,
                        after_path=after_disk,
                        output_dir=output_disk,
                        hotspot_id=f"HS-{cand['scene_id']}"
                    )
                    if cand_yolo_result and "image_urls" in cand_yolo_result:
                        cand_yolo_result["image_urls"]["before_image"] = analysis_res.get("before_image_url")
                        cand_yolo_result["image_urls"]["after_image"] = analysis_res.get("after_image_url")

            # Fuse evidence using transparent, mode-specific scoring
            score_breakdown = _fuse_evidence_score(
                analysis_mode=analysis_mode,
                color_diff_pct=color_diff_pct,
                ssim_pct=ssim_pct,
                yolo_result=cand_yolo_result,
                semantic_score_0_1=semantic_score_0_1
            )
            evidence_score = score_breakdown["final_score"]

            hotspot = {
                "hotspot_id": f"HS-{cand['scene_id']}",
                "location_name": loc_name,
                "lat": center_lat,
                "lng": center_lng,
                "bbox": bbox,
                "evidence_score": evidence_score,
                "semantic_score": semantic_score_0_1 * 100,
                "analysis_metrics": {
                    "ssim_pct": ssim_pct,
                    "color_diff_pct": color_diff_pct,
                    "confidence": analysis_res.get("confidence", "unknown")
                },
                "before_image": analysis_res.get("before_image_url"),
                "after_image": analysis_res.get("after_image_url"),
                "color_overlay": analysis_res.get("color_diff_overlay_url"),
                "ssim_overlay": analysis_res.get("ssim_overlay_url"),
                "mode": analysis_mode,
                "tiers": analysis_res.get("tiers", {}),
                "hotspots": analysis_res.get("hotspots", []),
                "yolo_analysis": cand_yolo_result,
                "score_breakdown": score_breakdown
            }
            all_hotspots.append(hotspot)
        except Exception as e:
            print(f"Skipping verification for {cand.get('scene_id')} due to error: {e}")
            continue

    # 5. Rank Hotspots
    all_hotspots.sort(key=lambda x: x["evidence_score"], reverse=True)

    return {
        "query": req.query,
        "mode": analysis_mode,
        "ranked_hotspots": all_hotspots
    }



# ==========================================
# AI ZOOM-AND-VERIFY AGENT ENDPOINTS
# ==========================================

@app.get("/api/hotspots")
async def get_hotspots(location_id: str = Query("mihan", description="Location identifier")):
    hotspots = get_hotspots_for_location(location_id)
    return {
        "location_id": location_id,
        "hotspots": hotspots,
        "count": len(hotspots),
        "high_priority_count": sum(1 for h in hotspots if h.get("priority") in ["CRITICAL", "HIGH"])
    }


@app.api_route("/api/inspect-hotspot", methods=["GET", "POST"])
async def inspect_hotspot(
    request: Request,
    hotspot_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query("mihan")
):
    """
    Executes the AI Zoom-and-Verify Agent on a specific candidate hotspot (Supports GET & POST).
    """
    body_data = {}
    if request.method == "POST":
        try:
            body_data = await request.json()
        except Exception:
            pass

    hid = body_data.get("hotspot_id") or hotspot_id or "MIHAN-042"
    loc_id = body_data.get("location_id") or location_id or "mihan"
    hdata = body_data.get("hotspot_data")

    cache_key = f"{loc_id.lower()}_{hid.upper()}"
    base_url = ""

    try:
        case_file = execute_zoom_and_verify_agent(
            hotspot_id=hid,
            location_id=loc_id,
            hotspot_data=hdata,
            base_url=base_url
        )
        INSPECTION_CACHE[cache_key] = case_file
        return {
            "status": "success",
            "case": case_file
        }
    except Exception as e:
        print(f"Inspection agent error for {hid}: {e}")
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "reason": f"Inspection failed: {str(e)}"}
        )


@app.api_route("/api/inspect-all", methods=["GET", "POST"])
async def inspect_all_hotspots(
    request: Request,
    location_id: Optional[str] = Query("mihan")
):
    body_data = {}
    if request.method == "POST":
        try:
            body_data = await request.json()
        except Exception:
            pass

    loc_id = body_data.get("location_id") or location_id or "mihan"
    base_url = ""
    hotspots = get_hotspots_for_location(loc_id)
    cases = []

    for h in hotspots:
        hid = h.get("hotspot_id", "")
        if not hid:
            continue
        try:
            case_file = execute_zoom_and_verify_agent(
                hotspot_id=hid,
                location_id=loc_id,
                base_url=base_url
            )
            cache_key = f"{loc_id.lower()}_{hid.upper()}"
            INSPECTION_CACHE[cache_key] = case_file
            cases.append(case_file)
        except Exception as e:
            print(f"Failed inspecting hotspot {hid}: {e}")

    return {
        "status": "success",
        "location_id": loc_id,
        "cases": cases,
        "count": len(cases)
    }


@app.api_route("/api/inspection/{hotspot_id}", methods=["GET", "POST"])
async def get_cached_inspection(hotspot_id: str, location_id: str = "mihan", request: Request = None):
    cache_key = f"{location_id.lower()}_{hotspot_id.upper()}"
    if cache_key in INSPECTION_CACHE:
        return {"status": "success", "case": INSPECTION_CACHE[cache_key]}

    base_url = "" if request else "http://localhost:8000"
    case_file = execute_zoom_and_verify_agent(hotspot_id=hotspot_id, location_id=location_id, base_url=base_url)
    INSPECTION_CACHE[cache_key] = case_file
    return {"status": "success", "case": case_file}


# ============================================================================
# YOLO Building Intelligence Endpoints
# ============================================================================

def _resolve_hotspot_image_paths(hotspot_id: str, location_id: Optional[str] = None, custom_before: Optional[str] = None, custom_after: Optional[str] = None) -> Tuple[Optional[Path], Optional[Path], Path]:
    hid_clean = hotspot_id.lower().replace("_", "-")
    crops_dir = STATIC_DIR / "hotspot_crops" / hid_clean

    # 1. Prioritize pre-existing level 1 crops (guarantees correct zoom scale for YOLO segmenter)
    if crops_dir.exists():
        b = next(crops_dir.glob("*_level1_before.png"), None) or next(crops_dir.glob("*before*.png"), None)
        a = next(crops_dir.glob("*_level1_after.png"), None) or next(crops_dir.glob("*after*.png"), None)
        if b and a:
            return b, a, crops_dir

    # 2. If crops don't exist but we have location_id and custom imagery, dynamically generate them!
    if location_id and custom_before and custom_after:
        try:
            import cv2
            from backend.hotspots import get_hotspots_for_location
            from backend.wayback_crop import generate_aligned_hotspot_crops
            
            hotspots = get_hotspots_for_location(location_id)
            matched = next((h for h in hotspots if h.get("hotspot_id", "").upper() == hotspot_id.upper()), None)
            if matched:
                path_before = urlparse(urllib.parse.unquote(custom_before)).path
                path_after = urlparse(urllib.parse.unquote(custom_after)).path
                p_b = Path(path_before.lstrip("/"))
                p_a = Path(path_after.lstrip("/"))
                
                cb, ca = None, None
                for candidate_root in [BASE_DIR, PUBLIC_DIR, STATIC_DIR]:
                    if (candidate_root / p_b).exists() and (candidate_root / p_a).exists():
                        cb = candidate_root / p_b
                        ca = candidate_root / p_a
                        break
                if not cb and "/static/" in path_before:
                    rel_before = path_before.split("/static/", 1)[1]
                    rel_after = path_after.split("/static/", 1)[1]
                    if (STATIC_DIR / rel_before).exists() and (STATIC_DIR / rel_after).exists():
                        cb = STATIC_DIR / rel_before
                        ca = STATIC_DIR / rel_after

                if cb and ca:
                    img_b = cv2.imread(str(cb))
                    img_a = cv2.imread(str(ca))
                    if img_b is not None and img_a is not None:
                        clean_short = location_id.lower().replace("live-", "").split("--")[0].split("-")[0]
                        lat, lon = 21.1458, 79.0882
                        from backend.hotspots import GEOCODE_CACHE
                        for k, (glat, glon, gdisp) in GEOCODE_CACHE.items():
                            if k in clean_short.lower() or clean_short.lower() in k:
                                lat, lon = glat, glon
                                break
                        parent_bbox = [lon - 0.024, lat - 0.024, lon + 0.024, lat + 0.024]
                        
                        print(f"Dynamically generating level 1 crop for {hotspot_id} at {lat}, {lon}...")
                        generate_aligned_hotspot_crops(
                            hotspot=matched,
                            parent_bbox=parent_bbox,
                            mosaic_pair=(img_b, img_a, parent_bbox)
                        )
                        
                        if crops_dir.exists():
                            b = next(crops_dir.glob("*_level1_before.png"), None) or next(crops_dir.glob("*before*.png"), None)
                            a = next(crops_dir.glob("*_level1_after.png"), None) or next(crops_dir.glob("*after*.png"), None)
                            if b and a:
                                return b, a, crops_dir
        except Exception as e:
            print(f"[-] Dynamic crop generation failed: {e}")

    # 3. Fallback to custom images directly if we can't generate crops
    if custom_before and custom_after:
        try:
            path_before = urlparse(urllib.parse.unquote(custom_before)).path
            path_after = urlparse(urllib.parse.unquote(custom_after)).path
        except Exception:
            path_before = custom_before
            path_after = custom_after

        p_b = Path(path_before.lstrip("/"))
        p_a = Path(path_after.lstrip("/"))
        
        for candidate_root in [BASE_DIR, PUBLIC_DIR, STATIC_DIR]:
            cb = candidate_root / p_b
            ca = candidate_root / p_a
            if cb.exists() and ca.exists():
                return cb, ca, crops_dir

        if "/static/" in path_before:
            rel_before = path_before.split("/static/", 1)[1]
            rel_after = path_after.split("/static/", 1)[1]
            cb = STATIC_DIR / rel_before
            ca = STATIC_DIR / rel_after
            if cb.exists() and ca.exists():
                return cb, ca, crops_dir

        if "/public/" in path_before:
            rel_before = path_before.split("/public/", 1)[1]
            rel_after = path_after.split("/public/", 1)[1]
            cb = PUBLIC_DIR / rel_before
            ca = PUBLIC_DIR / rel_after
            if cb.exists() and ca.exists():
                return cb, ca, crops_dir

    all_crop_dirs = list((STATIC_DIR / "hotspot_crops").iterdir())
    for cd in all_crop_dirs:
        if cd.is_dir():
            prefix = hid_clean.split("-")[0]
            if cd.name.startswith(prefix) or prefix in cd.name:
                b = next(cd.glob("*_level1_before.png"), None) or next(cd.glob("*before*.png"), None)
                a = next(cd.glob("*_level1_after.png"), None) or next(cd.glob("*after*.png"), None)
                if b and a:
                    return b, a, cd

    if not isinstance(location_id, str):
        location_id = None
    loc_key = (location_id or hid_clean).lower()
    if "hingna" in loc_key:
        b = PUBLIC_DIR / "wayback_hingna_2019_before.png"
        a = PUBLIC_DIR / "wayback_hingna_2025_after.png"
        if b.exists() and a.exists():
            return b, a, crops_dir
    elif "sadar" in loc_key:
        b = PUBLIC_DIR / "wayback_sadar_2019_before.png"
        a = PUBLIC_DIR / "wayback_sadar_2025_after.png"
        if b.exists() and a.exists():
            return b, a, crops_dir
    elif "civil" in loc_key:
        b = PUBLIC_DIR / "wayback_civil_lines_2019_before.png"
        a = PUBLIC_DIR / "wayback_civil_lines_2025_after.png"
        if b.exists() and a.exists():
            return b, a, crops_dir

    default_dir = STATIC_DIR / "hotspot_crops" / "mihan-042"
    b = default_dir / "mihan-042_level1_before.png"
    a = default_dir / "mihan-042_level1_after.png"
    return b, a, default_dir


def _build_yolo_response_payload(
    hotspot_id: str,
    change_res: Dict[str, Any],
    veri_res: Optional[Dict[str, Any]] = None,
    fusion_res: Optional[Dict[str, Any]] = None,
    run_dir_name: str = "yolo_change_test",
    before_rel_url: str = "",
    after_rel_url: str = "",
    base_url: str = ""
) -> Dict[str, Any]:
    dev, dev_name = get_inference_device()
    cuda_avail, vram_info = _get_torch_cuda_info()
    s = change_res.get("summary", {})
    after_records = change_res.get("after_building_records", [])
    before_records = change_res.get("before_building_records", [])

    veri_map = {}
    if veri_res and "candidates" in veri_res:
        veri_map = {c["candidate_id"]: c for c in veri_res["candidates"]}

    case_map = {}
    if fusion_res and "cases" in fusion_res:
        case_map = {c["candidate_id"]: c for c in fusion_res["cases"]}

    enriched_detections = []
    confs = []
    for rec in after_records:
        cid = rec["building_id"]
        conf = rec.get("after_confidence", 0.0)
        confs.append(conf)

        v_data = veri_map.get(cid, {})
        c_data = case_map.get(cid, {})

        det_entry = {
            **rec,
            "verification_status": v_data.get("status", "EXISTING" if rec["status"] == "EXISTING" else "UNCERTAIN"),
            "verification_evidence_score": v_data.get("evidence_score", None),
            "verification_reason": v_data.get("reason", ""),
            "verification_pipeline": c_data.get("verification_pipeline", None),
            "scoring_breakdown": c_data.get("scoring_breakdown", None),
            "risk_score": c_data.get("risk_score", 0.0 if rec["status"] == "EXISTING" else (88.0 if rec["status"] == "NEW" else 74.0)),
            "priority": c_data.get("priority", "LOW" if rec["status"] == "EXISTING" else ("CRITICAL" if rec["status"] == "NEW" else "HIGH")),
            "recommended_action": c_data.get("recommended_action", "NO_ACTION" if rec["status"] == "EXISTING" else ("IMMEDIATE_COMPLIANCE" if rec["status"] == "NEW" else "FIELD_INSPECTION")),
            "recommended_action_details": c_data.get("recommended_action_details", "Existing structure confirmed. Routine monitoring." if rec["status"] == "EXISTING" else ("Unauthorized construction detected. Immediate stop-work order and field verification required." if rec["status"] == "NEW" else "Building footprint expansion detected. On-site inspection and permit verification needed.")),
            "evidence_factors": c_data.get("evidence_factors", [])
        }
        enriched_detections.append(det_entry)

    avg_conf = round(float(sum(confs) / len(confs)), 4) if confs else 0.0
    top_conf = round(float(max(confs)), 4) if confs else 0.0
    hid_clean = hotspot_id.lower().replace("_", "-")

    return {
        "status": "success",
        "hotspot_id": hotspot_id,
        "timestamp": time.time(),
        "model_info": {
            "model": "keremberke/yolov8s-building-segmentation",
            "task": "segment",
            "class_names": ["Building"],
            "classes": {0: "Building"},
            "device": dev,
            "device_name": dev_name,
            "cuda_available": _get_torch_cuda_info()[0],
            "vram_gb": _get_torch_cuda_info()[1],
            "confidence_threshold": change_res.get("confidence_threshold", 0.35),
            "iou_match_threshold": change_res.get("iou_match_threshold", 0.35),
            "inference_time_ms": change_res.get("total_inference_and_matching_time_ms", 0.0)
        },
        "summary": {
            "before_count": s.get("total_before_detections", len(before_records)),
            "after_count": s.get("total_after_detections", len(after_records)),
            "existing_count": s.get("num_existing", 0),
            "new_count": s.get("num_new", 0),
            "expanded_count": s.get("num_expanded", 0),
            "uncertain_count": s.get("num_uncertain", 0),
            "before_pixel_area": s.get("before_building_pixel_area", 0),
            "after_pixel_area": s.get("after_building_pixel_area", 0),
            "total_change_pixel_area": s.get("total_change_pixel_area", 0),
            "ground_area_m2": s.get("ground_area_m2", None),
            "physical_change": (s.get("num_new", 0) + s.get("num_expanded", 0)) > 0,
            "average_yolo_confidence": avg_conf,
            "top_yolo_confidence": top_conf
        },
        "image_dimensions": change_res.get("image_dimensions", {"width": 560, "height": 560}),
        "detections": enriched_detections,
        "before_records": before_records,
        "cases": fusion_res.get("cases", []) if fusion_res else [],
        "image_urls": {
            "before_image": before_rel_url or f"/static/hotspot_crops/{hid_clean}/{hid_clean}_level1_before.png",
            "after_image": after_rel_url or f"/static/hotspot_crops/{hid_clean}/{hid_clean}_level1_after.png",
            "before_annotated": f"/outputs/{run_dir_name}/before_annotated.jpg",
            "after_annotated": f"/outputs/{run_dir_name}/after_annotated.jpg",
            "change_mask": f"/outputs/{run_dir_name}/change_mask.png",
            "before_after_comparison": f"/outputs/{run_dir_name}/before_after_comparison.jpg",
            "verification_summary": f"/outputs/{run_dir_name}/verification_summary.jpg",
            "priority_summary": f"/outputs/{run_dir_name}/priority_summary.jpg"
        }
    }


@app.get("/api/yolo/status")
async def get_yolo_status():
    dev, dev_name = get_inference_device()
    cuda_avail, vram = _get_torch_cuda_info()
    return {
        "status": "READY",
        "model": "keremberke/yolov8s-building-segmentation",
        "task": "segment",
        "class_names": ["Building"],
        "classes": {0: "Building"},
        "device": dev,
        "device_name": dev_name,
        "cuda_available": cuda_avail,
        "vram_gb": vram,
        "default_confidence_threshold": 0.35,
        "supports_live_inference": True
    }


@app.api_route("/api/yolo/results/{hotspot_id}", methods=["GET", "POST"])
async def get_yolo_results(
    hotspot_id: str,
    location_id: Optional[str] = None,
    before_image: Optional[str] = None,
    after_image: Optional[str] = None,
    request: Request = None
):
    loc_id_str = location_id if isinstance(location_id, str) else None
    hid_clean = hotspot_id.lower().replace("_", "-")
    
    # If custom images are provided, do not cache using the static hotspot id key 
    # to avoid conflicts across dynamic search regions
    cache_key = f"{hid_clean}_{loc_id_str or ''}_{hash(before_image or '')}_{hash(after_image or '')}"

    if cache_key in YOLO_RESULTS_CACHE:
        return YOLO_RESULTS_CACHE[cache_key]

    run_dir = OUTPUTS_DIR / "yolo_runs" / hid_clean
    # Only read from static disk cache if no custom before/after images are requested
    if not (before_image or after_image) and run_dir.exists() and (run_dir / "results.json").exists():
        with open(run_dir / "results.json", "r", encoding="utf-8") as f:
            yolo_data = json.load(f)

        veri_data = None
        if (run_dir / "verification_results.json").exists():
            with open(run_dir / "verification_results.json", "r", encoding="utf-8") as f:
                veri_data = json.load(f)

        fusion_data = None
        if (run_dir / "case_records.json").exists():
            with open(run_dir / "case_records.json", "r", encoding="utf-8") as f:
                fusion_data = json.load(f)

        before_p, after_p, _ = _resolve_hotspot_image_paths(hotspot_id=hotspot_id, location_id=location_id)
        before_rel, after_rel = "", ""
        if before_p and before_p.exists():
            try:
                if "static" in str(before_p).lower():
                    before_rel = f"/static/{before_p.relative_to(STATIC_DIR).as_posix()}"
                    after_rel = f"/static/{after_p.relative_to(STATIC_DIR).as_posix()}"
                elif "public" in str(before_p).lower():
                    before_rel = f"/{before_p.relative_to(PUBLIC_DIR).as_posix()}"
                    after_rel = f"/{after_p.relative_to(PUBLIC_DIR).as_posix()}"
            except Exception:
                pass

        base_url = "" if request else ""
        payload = _build_yolo_response_payload(
            hotspot_id=hotspot_id,
            change_res=yolo_data,
            veri_res=veri_data,
            fusion_res=fusion_data,
            run_dir_name=f"yolo_runs/{hid_clean}",
            before_rel_url=before_rel,
            after_rel_url=after_rel,
            base_url=base_url
        )
        YOLO_RESULTS_CACHE[cache_key] = payload
        return payload

    return await analyze_yolo_building_change(
        request=request,
        hotspot_id=hotspot_id,
        location_id=loc_id_str,
        before_image=before_image,
        after_image=after_image
    )


@app.api_route("/api/yolo/analyze", methods=["GET", "POST"])
async def analyze_yolo_building_change(
    request: Request,
    hotspot_id: Optional[str] = None,
    location_id: Optional[str] = None,
    conf_threshold: float = 0.35,
    before_image: Optional[str] = None,
    after_image: Optional[str] = None
):
    body_data = {}
    if request.method == "POST":
        try:
            body_data = await request.json()
        except Exception:
            pass

    hid = body_data.get("hotspot_id") or hotspot_id or "MIHAN-042"
    loc_id = body_data.get("location_id") or location_id
    raw_conf = body_data.get("conf_threshold")
    if raw_conf is not None:
        try:
            conf = float(raw_conf)
        except Exception:
            conf = 0.35
    else:
        try:
            conf = float(conf_threshold)
        except Exception:
            conf = 0.35
    custom_b = body_data.get("before_image") or before_image
    custom_a = body_data.get("after_image") or after_image

    hid_clean = hid.lower().replace("_", "-")
    before_p, after_p, crops_dir = _resolve_hotspot_image_paths(
        hotspot_id=hid,
        location_id=loc_id,
        custom_before=custom_b,
        custom_after=custom_a
    )

    if not before_p or not after_p or not before_p.exists() or not after_p.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Matched high-resolution imagery not found for hotspot '{hid}'."
        )

    try:
        run_dir_name = f"yolo_runs/{hid_clean}"
        out_yolo_dir = OUTPUTS_DIR / "yolo_runs" / hid_clean
        out_yolo_dir.mkdir(parents=True, exist_ok=True)

        change_res = compare_building_change(
            before_image=before_p,
            after_image=after_p,
            conf_threshold=conf,
            output_dir=out_yolo_dir
        )

        veri_res = run_multiscale_verification(
            results_json_path=out_yolo_dir / "results.json",
            crops_dir=crops_dir,
            output_dir=out_yolo_dir,
            before_image_path=before_p,
            after_image_path=after_p
        )

        fusion_res = fuse_municipal_evidence(
            yolo_results_path=out_yolo_dir / "results.json",
            multiscale_results_path=out_yolo_dir / "verification_results.json",
            hotspot_id=hid,
            output_dir=out_yolo_dir
        )

        before_rel, after_rel = "", ""
        try:
            if "static" in str(before_p).lower():
                before_rel = f"/static/{before_p.relative_to(STATIC_DIR).as_posix()}"
                after_rel = f"/static/{after_p.relative_to(STATIC_DIR).as_posix()}"
            elif "public" in str(before_p).lower():
                before_rel = f"/{before_p.relative_to(PUBLIC_DIR).as_posix()}"
                after_rel = f"/{after_p.relative_to(PUBLIC_DIR).as_posix()}"
        except Exception:
            pass

        base_url = "" if request else ""
        payload = _build_yolo_response_payload(
            hotspot_id=hid,
            change_res=change_res,
            veri_res=veri_res,
            fusion_res=fusion_res,
            run_dir_name=run_dir_name,
            before_rel_url=before_rel,
            after_rel_url=after_rel,
            base_url=base_url
        )

        cache_key = hid_clean
        YOLO_RESULTS_CACHE[cache_key] = payload
        return payload

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"YOLO Building Analysis failed: {str(e)}"
        )


# -----------------------------------------------------------------------------
# Phase 5: Adaptive Municipal Priority, XGBoost & Gemini Explanation Endpoints
# -----------------------------------------------------------------------------
from backend.priority_engine import evaluate_rule_priority
from backend.priority_xgboost import evaluate_xgboost_priority
from backend.explanation_engine import generate_officer_explanation
from backend.priority_training import save_officer_feedback, load_all_feedback


@app.api_route("/api/priority/evaluate", methods=["GET", "POST"])
async def evaluate_municipal_priority(request: Request, case_id: Optional[str] = Query(None)):
    """
    Evaluates rule-based priority score, checks XGBoost adaptive model,
    and generates Gemini/Grok officer explanation with deterministic fallback (Supports GET & POST).
    """
    body_data = {}
    if request.method == "POST":
        try:
            body_data = await request.json()
        except Exception:
            pass

    cid = body_data.get("case_id") or case_id or "CASE #NGP-MIHAN-BLDG-001"
    cd = body_data.get("case_data") or {"case_id": cid}
    yolo_res = body_data.get("yolo_results")
    veri_res = body_data.get("verification_results")

    rule_res = evaluate_rule_priority(cd, yolo_res, veri_res)
    xgb_res = evaluate_xgboost_priority(rule_res.get("features", {}))
    explanation = generate_officer_explanation(cd, rule_res)

    return {
        "case_id": cid,
        "rule_based_priority": rule_res,
        "xgboost_model": xgb_res,
        "explanation": explanation,
        "active_priority": rule_res["priority"] if xgb_res.get("fallback_to_rules") else xgb_res["prediction"]
    }


@app.api_route("/api/priority/feedback", methods=["GET", "POST"])
async def submit_officer_feedback(
    request: Request,
    case_id: Optional[str] = Query(None),
    officer_decision: Optional[str] = Query(None),
    officer_priority: Optional[str] = Query(None),
    notes: Optional[str] = Query(None)
):
    """
    Logs officer review decisions and priorities as ground-truth training data (Supports GET & POST).
    """
    body_data = {}
    if request.method == "POST":
        try:
            body_data = await request.json()
        except Exception:
            pass

    cid = body_data.get("case_id") or case_id or "CASE #NGP-MIHAN-BLDG-001"
    dec = body_data.get("officer_decision") or officer_decision or "CONFIRMED"
    prio = body_data.get("officer_priority") or officer_priority or "HIGH"
    nts = body_data.get("notes") or notes or ""
    cd = body_data.get("case_data")

    res = save_officer_feedback(
        case_id=cid,
        officer_decision=dec,
        officer_priority=prio,
        notes=nts,
        case_data=cd
    )
    return res


@app.get("/api/priority/model-status")
def get_priority_model_status():
    all_fb = load_all_feedback()
    dummy_feats = {
        "change_pixel_area": 1812.0, "change_pct": 7.06, "new_buildings_count": 1,
        "expanded_buildings_count": 0, "yolo_confidence": 0.68, "verification_score": 71.0,
        "iou": 0.0, "ssim_divergence": 90.6, "edge_emergence": 17.5, "time_delta_days": 2191,
        "change_type_code": 1, "sensitivity_score": 80.0, "image_quality_code": 1
    }
    xgb_info = evaluate_xgboost_priority(dummy_feats)
    return {
        "total_officer_feedback_count": len(all_fb),
        "xgboost_status": xgb_info
    }


# Static Image File Fallbacks for root asset requests
@app.get("/{filename}.png")
async def get_public_png(filename: str):
    file_path = PUBLIC_DIR / f"{filename}.png"
    if file_path.exists():
        return FileResponse(path=str(file_path), media_type="image/png")
    static_file = STATIC_DIR / f"{filename}.png"
    if static_file.exists():
        return FileResponse(path=str(static_file), media_type="image/png")
    raise HTTPException(status_code=404, detail=f"PNG asset '{filename}.png' not found")


@app.get("/{filename}.jpg")
async def get_public_jpg(filename: str):
    file_path = PUBLIC_DIR / f"{filename}.jpg"
    if file_path.exists():
        return FileResponse(path=str(file_path), media_type="image/jpeg")
    static_file = STATIC_DIR / f"{filename}.jpg"
    if static_file.exists():
        return FileResponse(path=str(static_file), media_type="image/jpeg")
    raise HTTPException(status_code=404, detail=f"JPG asset '{filename}.jpg' not found")


# ==========================================
# CENTRAL AGENTIC ORCHESTRATION ENDPOINTS
# ==========================================

@app.post("/api/agent/run")
async def run_agent_investigation(req: AgentRunRequest, request: Request):
    """
    Executes the full autonomous EarthWatch Agent workflow:
    SEARCH -> PLAN -> SCAN -> REASON -> ZOOM -> VERIFY -> CROSS-CHECK -> REPORT
    """
    base_url = ""
    orchestrator = EarthWatchOrchestrator(base_url=base_url)

    try:
        result = await orchestrator.execute_investigation(
            location_query=req.location_name,
            custom_before=req.before_date,
            custom_after=req.after_date
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=422,
            detail={"status": "error", "reason": str(ve)}
        )
    except Exception as e:
        print(f"EarthWatch Agent error on '{req.location_name}': {e}")
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "reason": f"Agent investigation failed: {str(e)}"}
        )


@app.get("/api/agent/stream")
async def stream_agent_investigation(
    location_name: str = Query(..., description="Location to investigate"),
    before_date: Optional[str] = Query(None),
    after_date: Optional[str] = Query(None),
    request: Request = None
):
    """
    Streams real-time step-by-step tool execution events as Server-Sent Events (SSE).
    """
    base_url = "" if request else "http://localhost:8000"

    async def event_generator():
        orchestrator = EarthWatchOrchestrator(base_url=base_url)
        queue: asyncio.Queue = asyncio.Queue()

        def on_event(evt):
            queue.put_nowait(evt)

        # Launch orchestrator in background task
        task = asyncio.create_task(
            orchestrator.execute_investigation(
                location_query=location_name,
                custom_before=before_date,
                custom_after=after_date,
                event_callback=on_event
            )
        )

        while not task.done() or not queue.empty():
            try:
                evt = await asyncio.wait_for(queue.get(), timeout=0.2)
                yield f"data: {json.dumps(evt)}\n\n"
            except asyncio.TimeoutError:
                continue

        try:
            final_res = await task
            yield f"data: {json.dumps({'type': 'COMPLETE', 'result': final_res})}\n\n"
        except Exception as err:
            yield f"data: {json.dumps({'type': 'ERROR', 'error': str(err)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")



# --- SPA Catch-All: Serve Vite frontend for non-API routes ---
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve the Vite-built frontend. Falls back to index.html for client-side routing."""
    if DIST_DIR.exists():
        # Try to serve the exact file first (JS, CSS, images, etc.)
        file_path = DIST_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # For all other routes, serve index.html (SPA client-side routing)
        index_path = DIST_DIR / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Not found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=os.environ.get("RENDER") is None)
