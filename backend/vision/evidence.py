"""
Multi-Source Evidence Fusion Engine
Nagpur EarthWatch — Prototype Evidence-Fusion Scoring

Combines broad-scale Sentinel-2 multi-spectral differencing, SSIM structural matrices,
sub-meter Wayback optical deltas, and multimodal AI vision classifications into a
unified EarthWatch Composite Confidence score.
"""

from typing import Dict, Any, Tuple


def fuse_multi_source_evidence(
    sentinel_color_diff_pct: float,
    sentinel_ssim_pct: float,
    wayback_diff_pct: float,
    vision_confidence: int,
    spatial_consistency_score: float = 85.0
) -> Dict[str, Any]:
    """
    Computes prototype evidence-fusion score across all optical and AI sensor tiers.
    """
    # 1. Normalize individual tier inputs to 0-100 scales
    s2_score = min(100.0, sentinel_color_diff_pct * 8.5)
    ssim_score = min(100.0, sentinel_ssim_pct * 7.5)
    wb_score = min(100.0, wayback_diff_pct * 9.0)
    ai_score = float(vision_confidence)
    spatial_score = float(spatial_consistency_score)

    # 2. Linear prototype evidence weighting:
    # 25% 10m Sentinel + 35% 0.6m Wayback + 30% AI Vision + 10% Spatial Consistency
    composite_raw = (
        0.25 * ((s2_score + ssim_score) / 2.0) +
        0.35 * wb_score +
        0.30 * ai_score +
        0.10 * spatial_score
    )

    composite_score = int(round(max(30.0, min(98.0, composite_raw))))

    if composite_score >= 82:
        status = "HIGH CONFIDENCE"
        verdict = "Multiple independent satellite and vision methods confirm structural alteration."
    elif composite_score >= 60:
        status = "MEDIUM CONFIDENCE"
        verdict = "Moderate multi-sensor evidence; ground verification recommended."
    else:
        status = "NEEDS HUMAN REVIEW"
        verdict = "Significant optical variance or cloud/shadow ambiguity; human audit required."

    return {
        "composite_confidence": composite_score,
        "status": status,
        "confidence_name": "EarthWatch Composite Confidence",
        "prototype_tag": "Prototype evidence-fusion score",
        "verdict_summary": verdict,
        "score_breakdown": {
            "sentinel_10m_macro": round((s2_score + ssim_score) / 2.0, 1),
            "wayback_06m_highres": round(wb_score, 1),
            "ai_vision_inspection": round(ai_score, 1),
            "spatial_consistency": round(spatial_score, 1)
        }
    }
