"""
Automated Verification Test Suite
Nagpur EarthWatch — Universal Multi-Resolution AI Inspection Pipeline
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.wayback_live import check_wayback_availability, get_wayback_releases, get_wayback_imagery
from backend.hotspots import extract_hotspots_from_masks, get_hotspots_for_location
from backend.wayback_crop import generate_aligned_hotspot_crops
from backend.vision_inspector import evaluate_vision_inspection, execute_zoom_and_verify_agent, fuse_confidence_scores


def test_wayback_availability():
    print("\n[1/5] Testing Wayback Availability Service...")
    civil_lines_bbox = [79.060, 21.140, 79.100, 21.180]
    res = check_wayback_availability(civil_lines_bbox)
    print(f"  Status: {res['status']} | {res['message']} (Releases: {res['release_count']})")
    assert res["status"] in ["AVAILABLE", "LIMITED"], "Wayback availability check failed!"
    print("  ✓ Wayback availability service verified.")


def test_hotspot_extraction_and_ranking():
    print("\n[2/5] Testing Candidate Hotspot Extraction & Priority Engine...")
    hotspots = get_hotspots_for_location("mihan")
    assert len(hotspots) >= 4, "Expected at least 4 candidate hotspots for MIHAN"

    top = hotspots[0]
    print(f"  Top Candidate Hotspot: {top['hotspot_id']} - {top['name']}")
    print(f"  Priority: {top['priority']} (Score: {top['priority_score']}) | Area: {top['area_formatted']}")
    assert top["priority"] in ["CRITICAL", "HIGH"], "Top hotspot must be CRITICAL or HIGH priority"
    print("  ✓ Candidate hotspot extraction & ranking verified.")


def test_aligned_crops_and_zoom_levels():
    print("\n[3/5] Testing 4-Level Aligned Crop Generator...")
    hotspot = {
        "hotspot_id": "CIVILLINES-001",
        "latitude": 21.1550,
        "longitude": 79.0750,
        "location_id": "civillines",
        "bbox_wgs84": [79.065, 21.145, 79.085, 21.165]
    }
    crops = generate_aligned_hotspot_crops(hotspot)
    print(f"  Generated Zoom Levels: {list(crops.keys())}")
    assert "level1" in crops and "level2" in crops and "level3" in crops, "Missing zoom levels"
    print("  ✓ Multi-scale aligned crop generator verified.")


def test_vision_inspection_and_decision_logic():
    print("\n[4/5] Testing AI Vision Inspector & Decision Stopping Logic...")
    hotspot = {
        "hotspot_id": "CIVILLINES-001",
        "latitude": 21.1550,
        "longitude": 79.0750,
        "location_name": "Civil Lines, Nagpur",
        "area_m2": 7500.0,
        "change_percent": 68.5,
        "ssim_percent": 55.0,
        "initial_confidence": 84
    }
    eval_res = evaluate_vision_inspection(hotspot, {})
    print(f"  Change Typology: {eval_res['change_type_label']}")
    print(f"  Decision Level: {eval_res['decision_level']} | Decision: {eval_res['zoom_decision']}")
    print(f"  Finding: {eval_res['finding']}")
    print(f"  Permit Match: {eval_res['permit_status']}")
    assert eval_res["change_type"] in ["NEW_CONSTRUCTION", "LAND_SURFACE_CHANGE"], "Unexpected change type"
    print("  ✓ AI Vision Inspector decision logic verified.")


def test_end_to_end_agent_case_generation():
    print("\n[5/5] Testing Full End-to-End Agent Case Generation...")
    case_file = execute_zoom_and_verify_agent("MIHAN-042", location_id="mihan")
    print(f"  Case ID: {case_file['case_id']}")
    print(f"  Typology: {case_file['change_type_label']}")
    print(f"  Composite Confidence: {case_file['composite_confidence']}% ({case_file['status']})")
    print(f"  Action: {case_file['recommended_action']}")
    print(f"  Completed Stages: {len(case_file['stages'])} stages")
    assert case_file["composite_confidence"] >= 85, "Composite confidence score below threshold"
    assert len(case_file["stages"]) == 7, "Expected 7 completed inspection stages"
    print("  ✓ End-to-end agent case generation verified.")


if __name__ == "__main__":
    print("================================================================")
    print(" NAGPUR EARTHWATCH — UNIVERSAL MULTI-RESOLUTION TEST SUITE")
    print("================================================================")
    test_wayback_availability()
    test_hotspot_extraction_and_ranking()
    test_aligned_crops_and_zoom_levels()
    test_vision_inspection_and_decision_logic()
    test_end_to_end_agent_case_generation()
    print("\n🎉 ALL 5 VERIFICATION SUITES PASSED CLEANLY (100% SUCCESS)")
    print("================================================================")
