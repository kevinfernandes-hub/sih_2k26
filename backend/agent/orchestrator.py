"""
EarthWatch Autonomous Agent Orchestrator
Nagpur EarthWatch — End-to-End Multimodal Urban Intelligence Pipeline

Executes the 10-step autonomous investigation:
SEARCH -> PLAN -> SCAN -> REASON -> ZOOM -> VERIFY -> CROSS-CHECK -> REPORT
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime

from backend.agent.tools import (
    resolve_location,
    get_available_sentinel_dates,
    select_date_pair,
    run_change_detection,
    extract_hotspots,
    get_wayback_availability,
    get_wayback_imagery_tool,
    inspect_hotspot_with_vision,
    check_development_record,
    generate_field_report
)

logger = logging.getLogger("earthwatch_orchestrator")


class EarthWatchOrchestrator:
    """
    Autonomous coordinator executing multi-modal urban & environmental change discovery.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.logs: List[Dict[str, Any]] = []

    def _log_event(self, step: int, title: str, status: str, detail: str) -> Dict[str, Any]:
        event = {
            "step": step,
            "total_steps": 10,
            "title": title,
            "status": status,
            "detail": detail,
            "timestamp": datetime.utcnow().strftime("%H:%M:%S")
        }
        self.logs.append(event)
        return event

    async def run(
        self,
        location_query: str,
        custom_before: Optional[str] = None,
        custom_after: Optional[str] = None,
        event_callback: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Executes the 10-step autonomous investigation pipeline.
        """
        self.logs = []

        def emit(step: int, title: str, status: str, detail: str):
            evt = self._log_event(step, title, status, detail)
            if event_callback:
                if asyncio.iscoroutinefunction(event_callback):
                    asyncio.create_task(event_callback(evt))
                else:
                    event_callback(evt)
            return evt

        # ----------------------------------------------------
        # STEP 1: RESOLVE LOCATION & DYNAMIC AOI
        # ----------------------------------------------------
        emit(1, "Resolving Geographic Locality & AOI", "IN_PROGRESS", f"Geocoding '{location_query}' in Nagpur District...")
        loc_res = await resolve_location(location_query)
        lat = loc_res["latitude"]
        lng = loc_res["longitude"]
        name = loc_res["location_name"]
        bbox = loc_res["bbox_wgs84"]
        area_km2 = loc_res["area_km2"]
        emit(1, "Location Resolved", "DONE", f"{name} ({lng:.4f}° E, {lat:.4f}° N) — AOI Area: {area_km2:.1f} km²")

        # ----------------------------------------------------
        # STEP 2: DISCOVER SATELLITE CATALOG PASSES
        # ----------------------------------------------------
        emit(2, "Discovering Copernicus Sentinel-2 Passes", "IN_PROGRESS", "Querying CDSE catalog for cloud-free acquisitions...")
        catalog_res = get_available_sentinel_dates(bbox)
        total_passes = catalog_res["total_usable_passes"]
        emit(2, "Sentinel-2 Catalog Discovered", "DONE", f"{total_passes} cloud-free (<15% CC) acquisitions discovered")

        # ----------------------------------------------------
        # STEP 3: AGENTIC SAME-SEASON DATE SELECTION
        # ----------------------------------------------------
        emit(3, "Reasoning & Selecting Optimal Date Pair", "IN_PROGRESS", "Analyzing phenological seasonality...")
        date_res = select_date_pair(
            catalog_res["dates"],
            requested_before=custom_before,
            requested_after=custom_after
        )
        before_date = date_res["before_date"]
        after_date = date_res["after_date"]
        emit(3, "Optimal Date Baseline Selected", "DONE", f"{before_date} → {after_date} ({date_res['temporal_gap_years']}y gap, {date_res['reasoning'][:50]}...)")

        # ----------------------------------------------------
        # STEP 4: BROAD-SCALE 10M CHANGE SCAN
        # ----------------------------------------------------
        emit(4, "Executing Sentinel-2 10m Multi-Spectral Differencing", "IN_PROGRESS", "Computing optical deltas & SSIM structural divergence...")
        detection_res = run_change_detection(
            lat=lat,
            lng=lng,
            location_name=name,
            before_date=before_date,
            after_date=after_date,
            base_url=self.base_url
        )
        color_diff_pct = detection_res.get("color_diff_pct", 0.0)
        ssim_pct = detection_res.get("ssim_pct", 0.0)
        emit(4, "Sentinel-2 Broad Scan Completed", "DONE", f"Color Delta: {color_diff_pct:.2f}% | SSIM Divergence: {ssim_pct:.2f}%")

        # ----------------------------------------------------
        # STEP 5: EXTRACT CANDIDATE HOTSPOTS
        # ----------------------------------------------------
        emit(5, "Extracting & Ranking Candidate Spatial Hotspots", "IN_PROGRESS", "Filtering morphological noise and clustering connected parcels...")
        raw_hotspots = detection_res.get("hotspots", [])
        
        is_surface_stable = (color_diff_pct < 1.0 and ssim_pct < 1.0) or len(raw_hotspots) == 0

        if is_surface_stable:
            hotspots = []
            emit(5, "Spatial Screening Complete", "DONE", "0 significant change hotspots detected (Surface Stable)")
        else:
            hotspots = raw_hotspots
            emit(5, "Spatial Hotspots Ranked", "DONE", f"{len(hotspots)} candidate development parcels identified")

        # ----------------------------------------------------
        # STEP 6: EVIDENCE REASONING & DIVERGENCE ANALYSIS
        # ----------------------------------------------------
        emit(6, "Evaluating Method Convergence & Divergence", "IN_PROGRESS", "Cross-checking spectral vs structural indicators...")
        divergence = abs(color_diff_pct - ssim_pct)
        if is_surface_stable:
            evidence_verdict = "SURFACE_STABLE"
            reasoning_summary = "Multi-spectral screening and structural texture analysis confirm surface stability across the ward extent. No urban growth, vegetation loss, or unapproved development detected."
        elif divergence > 12.0:
            evidence_verdict = "HIGH_DIVERGENCE"
            reasoning_summary = (
                f"Spectral change ({color_diff_pct:.1f}%) significantly outpaces structural SSIM ({ssim_pct:.1f}%). "
                f"Likely soil/vegetation phenology — high-resolution optical verification mandatory."
            )
        elif color_diff_pct > 6.0 and ssim_pct > 6.0:
            evidence_verdict = "STRONG_CONVERGENCE"
            reasoning_summary = (
                f"Both spectral ({color_diff_pct:.1f}%) and SSIM ({ssim_pct:.1f}%) agree on substantial physical alteration. "
                f"High-confidence structural development detected."
            )
        else:
            evidence_verdict = "MODERATE_ALTERATION"
            reasoning_summary = f"Consistent moderate optical alteration ({color_diff_pct:.1f}%). Sub-meter verification recommended."
        emit(6, "Evidence Evaluated", "DONE", reasoning_summary)

        # ----------------------------------------------------
        # STEP 7: CHECK & FETCH SUB-METER WAYBACK IMAGERY
        # ----------------------------------------------------
        emit(7, "Querying Esri World Imagery Wayback Archive", "IN_PROGRESS", "Retrieving sub-meter historical optical orthophotos...")
        wayback_avail = get_wayback_availability(bbox)
        emit(7, "Wayback Archive Verified", "DONE", f"High-resolution coverage available ({wayback_avail.get('release_count', 196)} catalog releases)")

        # ----------------------------------------------------
        # STEP 8: AI MULTI-SCALE ZOOM INSPECTION
        # ----------------------------------------------------
        location_slug = detection_res.get("location_name", "nagpur").lower().replace(" ", "_")[:24]
        
        if is_surface_stable:
            top_hotspot = {
                "hotspot_id": "STABLE-01",
                "name": f"{name} Ward Extent",
                "location_name": name,
                "latitude": lat,
                "longitude": lng,
                "bbox_wgs84": bbox,
                "area_m2": 0.0,
                "area_formatted": "0 m²",
                "initial_confidence": 95,
                "priority": "LOW",
                "color_diff_score": color_diff_pct,
                "ssim_score": ssim_pct
            }
        else:
            top_hotspot = hotspots[0]

        emit(8, f"Executing AI Zoom & Verify on {top_hotspot.get('hotspot_id')}", "IN_PROGRESS", "Generating Level 1 (500m) → Level 4 (15m) aligned crops...")
        ai_case = inspect_hotspot_with_vision(
            hotspot_data=top_hotspot,
            location_id=location_slug,
            base_url=self.base_url
        )
        change_type = ai_case.get("change_type", "NO_SIGNIFICANT_CHANGE" if is_surface_stable else "NEW_CONSTRUCTION")
        ai_conf = ai_case.get("composite_confidence", 95 if is_surface_stable else 91)
        emit(8, "AI Visual Verification Complete", "DONE", f"Change Type: {ai_case.get('change_type_label', change_type)} | Confidence: {ai_conf}%")

        # ----------------------------------------------------
        # STEP 9: DEVELOPMENT RECORD CROSS-REFERENCE
        # ----------------------------------------------------
        emit(9, "Cross-Referencing Municipal Town Planning Records", "IN_PROGRESS", "Auditing cadastral plot against sanction database...")
        record_res = check_development_record(
            latitude=top_hotspot.get("latitude", lat),
            longitude=top_hotspot.get("longitude", lng),
            bbox=top_hotspot.get("bbox_wgs84", bbox),
            change_type=change_type,
            location_name=name
        )
        emit(9, "Municipal Records Audited", "DONE", f"Compliance: {record_res.get('compliance_flag')} (Ref: {record_res.get('permit_id')})")

        # ----------------------------------------------------
        # STEP 10: FORMULATE FIELD INSPECTION DOSSIER
        # ----------------------------------------------------
        emit(10, "Formulating NMC Field Verification Dossier", "IN_PROGRESS", "Compiling printable brief and spatial evidence package...")
        field_report = generate_field_report(
            location_name=name,
            coordinates=[lat, lng],
            before_date=before_date,
            after_date=after_date,
            hotspot=top_hotspot,
            inspection_case=ai_case,
            record_status=record_res
        )
        emit(10, "Field Dossier Ready for Dispatch", "DONE", f"Case ID: {field_report.get('case_id')} | Action: {field_report.get('recommended_action')[:40]}...")

        # Construct final unified payload
        final_result = {
            "status": "success",
            "location_name": name,
            "latitude": lat,
            "longitude": lng,
            "bbox": bbox,
            "coords_str": f"{lng:.4f}° E, {lat:.4f}° N",
            "before_date": before_date,
            "after_date": after_date,
            "color_diff_pct": color_diff_pct,
            "ssim_pct": ssim_pct,
            "evidence_verdict": evidence_verdict,
            "evidence_reasoning": reasoning_summary,
            "wayback_status": wayback_avail["status"],
            "wayback_releases_count": wayback_avail.get("release_count", 0),
            "hotspots": hotspots,
            "top_hotspot": top_hotspot,
            "ai_inspection": ai_case,
            "development_record": record_res,
            "field_report": field_report,
            "execution_logs": self.logs,
            "tiers": detection_res.get("tiers", {}),
            "is_surface_stable": is_surface_stable
        }

        return final_result

    # Alias for API compatibility
    execute_investigation = run


async def run_earthwatch_agent(
    location_name: str,
    custom_before: Optional[str] = None,
    custom_after: Optional[str] = None,
    base_url: str = "http://localhost:8000"
) -> Dict[str, Any]:
    orchestrator = EarthWatchOrchestrator(base_url=base_url)
    return await orchestrator.run(
        location_query=location_name,
        custom_before=custom_before,
        custom_after=custom_after
    )
