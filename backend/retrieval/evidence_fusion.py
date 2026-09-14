"""Evidence fusion for retrieval results and temporal change outputs."""

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional


@dataclass(frozen=True)
class EvidenceWeights:
    spectral_change: float = 0.30
    ssim_change: float = 0.25
    semantic_relevance: float = 0.20
    temporal_consistency: float = 0.15
    cv_confirmation: float = 0.10

    def __post_init__(self) -> None:
        values = (
            self.spectral_change,
            self.ssim_change,
            self.semantic_relevance,
            self.temporal_consistency,
            self.cv_confirmation,
        )
        if any(value < 0 for value in values) or abs(sum(values) - 1.0) > 1e-6:
            raise ValueError("Evidence weights must be non-negative and sum to 1")


def fuse_change_evidence(
    *,
    retrieval: Mapping[str, Any],
    temporal: Mapping[str, Any],
    change: Optional[Mapping[str, Any]] = None,
    weights: EvidenceWeights = EvidenceWeights(),
) -> Dict[str, Any]:
    """Fuse normalized retrieval, temporal, spectral, SSIM, and CV evidence.

    ``change`` may be the existing pipeline response. Missing optional CV
    evidence remains explicitly unconfirmed rather than being fabricated.
    """

    change_data = change or {}
    spectral = _percent_score(change_data.get("color_diff_pct", change_data.get("colorDiffPct", 0.0)))
    ssim = _percent_score(change_data.get("ssim_pct", change_data.get("ssimPct", 0.0)))
    semantic = _unit_score(retrieval.get("semantic_score", retrieval.get("final_score", 0.0)))
    temporal_consistency = _temporal_consistency(temporal)
    cv_confirmation = _unit_score(
        change_data.get("cv_confirmation", change_data.get("verification_score", 0.0)),
        percent=True,
    )
    confidence = (
        weights.spectral_change * spectral
        + weights.ssim_change * ssim
        + weights.semantic_relevance * semantic
        + weights.temporal_consistency * temporal_consistency
        + weights.cv_confirmation * cv_confirmation
    )
    before_date = temporal.get("before_date") or temporal.get("change_analysis", {}).get("before_date")
    after_date = temporal.get("after_date") or temporal.get("change_analysis", {}).get("after_date")
    return {
        "change_type": _change_type(retrieval),
        "confidence": round(confidence, 6),
        "before_date": before_date,
        "after_date": after_date,
        "area": change_data.get("area", change_data.get("change_area_m2")),
        "evidence": [
            {"name": "spectral_change", "score": round(spectral, 6)},
            {"name": "ssim_change", "score": round(ssim, 6)},
            {"name": "semantic_relevance", "score": round(semantic, 6)},
            {"name": "temporal_consistency", "score": round(temporal_consistency, 6)},
            {"name": "cv_confirmation", "score": round(cv_confirmation, 6)},
        ],
        "weights": {
            "spectral_change": weights.spectral_change,
            "ssim_change": weights.ssim_change,
            "semantic_relevance": weights.semantic_relevance,
            "temporal_consistency": weights.temporal_consistency,
            "cv_confirmation": weights.cv_confirmation,
        },
    }


def _change_type(retrieval: Mapping[str, Any]) -> str:
    parsed = retrieval.get("parsed_query", {})
    return str(parsed.get("change_type") or parsed.get("land_use") or "land_use_change")


def _temporal_consistency(temporal: Mapping[str, Any]) -> float:
    dates = temporal.get("dates") or temporal.get("timeline", {}).get("dates", [])
    return 1.0 if len(dates) >= 2 else 0.0


def _percent_score(value: Any) -> float:
    return _unit_score(value, percent=True)


def _unit_score(value: Any, *, percent: bool = False) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, numeric / 100.0 if percent or numeric > 1.0 else numeric))