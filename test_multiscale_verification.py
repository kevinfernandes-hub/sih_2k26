"""
Test Runner for Stage 2C Multi-Scale Construction Verification
Evaluates candidate NEW buildings on MIHAN-042 multi-scale Wayback crops.
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.multiscale_verifier import run_multiscale_verification


def main():
    print("=" * 70)
    print("Nagpur EarthWatch — Stage 2C Multi-Scale Verification Test")
    print("=" * 70)

    results_json = Path("outputs/yolo_change_test/results.json")
    crops_dir = Path("backend/static/hotspot_crops/mihan-042")
    output_dir = Path("outputs/multiscale_verification")

    print(f"[1] Reading Stage 2B Candidates from: {results_json.resolve()}")
    print(f"[2] Multi-Scale Wayback Crops Dir:     {crops_dir.resolve()}")
    print(f"[3] Target Verification Output Dir:    {output_dir.resolve()}")

    res = run_multiscale_verification(
        results_json_path=results_json,
        crops_dir=crops_dir,
        output_dir=output_dir
    )

    print(f"\n[4] Multi-Scale Verification Summary:")
    print(f"    - Total Candidates Evaluated: {res['total_candidates_evaluated']}")
    print(f"    - CONFIRMED_NEW (Score >= 80): {res['summary_counts']['CONFIRMED_NEW']}")
    print(f"    - UNCERTAIN (Score 50-79):     {res['summary_counts']['UNCERTAIN']}")
    print(f"    - NOT_CONFIRMED (Score < 50):  {res['summary_counts']['NOT_CONFIRMED']}")

    print("\n[5] Detailed Candidate Verification Breakdown:")
    for cand in res["candidates"]:
        cid = cand["candidate_id"]
        status = cand["status"]
        score = cand["evidence_score"]
        conf = cand["after_yolo_confidence"]
        ssim_div = cand["ssim_divergence_pct"]
        pix_diff = cand["mean_pixel_diff"]
        tex_em = cand["texture_emergence_pct"]
        levels = ", ".join(cand["available_zoom_levels"])

        print(f"\n  * {cid}:")
        print(f"    - Decision:          {status}")
        print(f"    - Evidence Score:    {score:.1f} / 100")
        print(f"    - YOLO Confidence:   {conf:.4f}")
        print(f"    - SSIM Divergence:   {ssim_div:.1f}%")
        print(f"    - Mean Pixel Shift:  {pix_diff:.2f} px")
        print(f"    - Texture Emergence: +{tex_em:.1f}% (Std: 2019={cand.get('intensity_std_before', 'N/A')} -> 2025={cand.get('intensity_std_after', 'N/A')})")
        print(f"    - Available Zooms:   {levels}")
        print(f"    - Reason:            {cand['reason']}")
        print(f"    - Visual Dossier:    {cand['saved_artifacts']['evidence_dossier']}")

    print(f"\n[6] Summary Image Generated: {res['summary_image']}")
    print(f"[7] Results JSON Generated:   {output_dir / 'verification_results.json'}")

    print("\n" + "=" * 70)
    print("Stage 2C Multi-Scale Verification Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
