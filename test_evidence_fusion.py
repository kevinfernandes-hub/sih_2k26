"""Focused tests for retrieval evidence fusion."""

from backend.retrieval.evidence_fusion import fuse_change_evidence


def test_fusion_returns_traceable_weighted_confidence():
    result = fuse_change_evidence(
        retrieval={
            "semantic_score": 0.9,
            "parsed_query": {"change_type": "new_construction"},
        },
        temporal={"dates": ["2024-01-10", "2025-04-18"]},
        change={"color_diff_pct": 40.0, "ssim_pct": 20.0, "cv_confirmation": 80.0, "area": 12450},
    )

    assert result["change_type"] == "new_construction"
    assert result["before_date"] is None
    assert result["confidence"] == 0.58
    assert result["area"] == 12450
    assert len(result["evidence"]) == 5