"""
Test Runner for Stage 3 Municipal Evidence Fusion
Generates explainable municipal inspection priority cases and summary artifacts.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.municipal_fusion import fuse_municipal_evidence


def main():
    print("=" * 70)
    print("Nagpur EarthWatch — Stage 3 Municipal Evidence Fusion Test")
    print("=" * 70)

    yolo_results = Path("outputs/yolo_change_test/results.json")
    multiscale_results = Path("outputs/multiscale_verification/verification_results.json")
    output_dir = Path("outputs/evidence_fusion")

    print(f"[1] Input YOLO Changes:        {yolo_results.resolve()}")
    print(f"[2] Input Multi-Scale Ev.:     {multiscale_results.resolve()}")
    print(f"[3] Target Evidence Fusion Dir: {output_dir.resolve()}")

    res = fuse_municipal_evidence(
        yolo_results_path=yolo_results,
        multiscale_results_path=multiscale_results,
        hotspot_id="MIHAN-042",
        output_dir=output_dir
    )

    print(f"\n[4] Municipal Cases Summary:")
    print(f"    - Target Corridor:          {res['target_corridor']} ({res['hotspot_id']})")
    print(f"    - Total Cases Generated:    {res['summary_counts']['total_cases']}")
    print(f"    - HIGH Priority Cases:      {res['summary_counts']['HIGH_priority']}")
    print(f"    - MEDIUM Priority Cases:    {res['summary_counts']['MEDIUM_priority']}")
    print(f"    - LOW Priority Cases:       {res['summary_counts']['LOW_priority']}")

    print("\n[5] Detailed Case Records:")
    for case in res["cases"]:
        print(f"\n  * {case['case_id']} ({case['candidate_id']}):")
        print(f"    - Priority:           {case['priority']} (Risk Score: {case['risk_score']:.1f}/100)")
        print(f"    - Physical Change:    {case['physical_change']} ({case['change_area_pixels']} px footprint)")
        print(f"    - YOLO Confidence:    {case['building_confidence']:.4f}")
        print(f"    - Verification Status:{case['verification_status']}")
        print(f"    - Recommended Action: {case['recommended_action']} ({case['recommended_action_details']})")
        print(f"    - Location Bounds:    {case['location']['coordinates']} | BBox: {case['location']['bbox_xyxy']}")
        print(f"    - Scoring Breakdown:  F1(YOLO)={case['scoring_breakdown']['f1_yolo_confidence_score']}, F2(MultiScale)={case['scoring_breakdown']['f2_multiscale_evidence_score']}, F3(SSIM)={case['scoring_breakdown']['f3_ssim_divergence_pct']}%, F4(Area)={case['scoring_breakdown']['f4_footprint_scale_factor']}, F5(Macro)={case['scoring_breakdown']['f5_macro_hotspot_severity']}")
        print("    - Evidence Factors:")
        for ef in case["evidence_factors"]:
            print(f"        * {ef}")

    print(f"\n[6] Summary Image Generated: {res['summary_image']}")
    print(f"[7] Case Records JSON:       {output_dir / 'case_records.json'}")

    print("\n" + "=" * 70)
    print("Stage 3 Municipal Evidence Fusion Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
