"""
Nagpur EarthWatch — Transparent Rule-Based Municipal Priority Engine
Phase 5: Configurable & Explainable Municipal Case Prioritization

Computes deterministic priority scores (0-100), maps them to municipal priority tiers,
enforces safety overrides (e.g. UNCERTAIN evidence -> NEEDS_REVIEW), and generates
structured human-readable reasons for municipal officers.
"""

from typing import Dict, Any, List, Tuple
from backend.priority_features import extract_priority_features


DEFAULT_SCORING_WEIGHTS = {
    "large_change_threshold": 2000.0,
    "medium_change_threshold": 800.0,
    "small_change_threshold": 250.0,
    "score_large_change": 30,
    "score_medium_change": 20,
    "score_small_change": 10,
    
    "score_strong_evidence": 25,
    "score_moderate_evidence": 15,
    "score_uncertain_evidence": 5,

    "score_new_structure": 20,
    "score_expansion_structure": 15,
    "score_other_change": 10,

    "score_high_sensitivity": 15,
    "score_normal_sensitivity": 5,

    "score_good_quality": 10,
    "score_poor_quality": 0,

    "threshold_critical": 80,
    "threshold_high": 60,
    "threshold_medium": 40
}


def evaluate_rule_priority(
    case_data: Dict[str, Any],
    yolo_results: Dict[str, Any] = None,
    verification_results: Dict[str, Any] = None,
    weights: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Evaluates rule-based priority score, applies governance overrides,
    and returns structured priority & explanation reasons.
    """
    cfg = {**DEFAULT_SCORING_WEIGHTS, **(weights or {})}
    feats = extract_priority_features(case_data, yolo_results, verification_results)

    score = 0
    reasons: List[str] = []

    # 1. Physical Change Factor
    area = feats["change_pixel_area"]
    if area >= cfg["large_change_threshold"]:
        score += cfg["score_large_change"]
        reasons.append(f"Large physical change footprint detected (~{int(area):,} px)")
    elif area >= cfg["medium_change_threshold"]:
        score += cfg["score_medium_change"]
        reasons.append(f"Moderate physical structure change (~{int(area):,} px)")
    elif area >= cfg["small_change_threshold"]:
        score += cfg["score_small_change"]
        reasons.append(f"Localized structural change detected (~{int(area):,} px)")
    else:
        score += 5
        reasons.append("Minor physical surface variance observed")

    # 2. Evidence Strength Factor
    veri_score = feats["verification_score"]
    conf = feats["yolo_confidence"]
    if veri_score >= 75 or conf >= 0.75:
        score += cfg["score_strong_evidence"]
        reasons.append("Strong multi-modal imagery cross-verification (High Evidence)")
        evidence_tier = "STRONG"
    elif veri_score >= 50 or conf >= 0.50:
        score += cfg["score_moderate_evidence"]
        reasons.append("Moderate supporting imagery evidence (Verified)")
        evidence_tier = "MODERATE"
    else:
        score += cfg["score_uncertain_evidence"]
        reasons.append("Uncertain imagery signal requiring close inspection")
        evidence_tier = "UNCERTAIN"

    # 3. Change Type Factor
    ctype = feats["change_type_raw"]
    if feats["change_type_code"] == 1: # NEW
        score += cfg["score_new_structure"]
        reasons.append("New physical building emergence (Zero Baseline Match)")
    elif feats["change_type_code"] == 2: # EXPANDED
        score += cfg["score_expansion_structure"]
        reasons.append("Footprint expansion onto baseline property boundary")
    else:
        score += cfg["score_other_change"]
        reasons.append("Structural footprint alteration observed")

    # 4. Municipal Context & Sensitivity Factor
    if feats["sensitivity_score"] >= 75:
        score += cfg["score_high_sensitivity"]
        reasons.append(f"High-priority municipal surveillance corridor (Ward {feats['ward']} / {feats['zone']})")
    else:
        score += cfg["score_normal_sensitivity"]
        reasons.append(f"Monitored municipal zone (Ward {feats['ward']})")

    # 5. Image Quality Factor
    if feats["image_quality_code"] == 1:
        score += cfg["score_good_quality"]
    else:
        reasons.append("Sub-meter satellite imagery quality uncalibrated")

    # Final Score Bounding
    score = int(max(0, min(100, score)))

    # Initial Tier Determination
    if score >= cfg["threshold_critical"]:
        priority = "CRITICAL"
    elif score >= cfg["threshold_high"]:
        priority = "HIGH"
    elif score >= cfg["threshold_medium"]:
        priority = "MEDIUM"
    else:
        priority = "LOW"

    # 6. Safety Overrides (Uncertainty & Quality Controls)
    is_overridden = False
    override_reason = ""

    if evidence_tier == "UNCERTAIN":
        priority = "NEEDS_REVIEW"
        is_overridden = True
        override_reason = "Priority adjusted to NEEDS_REVIEW due to uncertain imagery verification evidence."
        reasons.append(override_reason)
    elif feats["image_quality_code"] == 0:
        priority = "NEEDS_REVIEW"
        is_overridden = True
        override_reason = "Priority set to NEEDS_REVIEW due to uncalibrated image quality."
        reasons.append(override_reason)

    recommended_action = (
        "FIELD INSPECTION REQUIRED" if priority in ["CRITICAL", "HIGH"] else
        "OFFICER REVIEW REQUIRED" if priority == "NEEDS_REVIEW" else
        "ROUTINE MONITORING"
    )

    return {
        "priority": priority,
        "priority_score": score,
        "evidence_strength": evidence_tier,
        "recommended_action": recommended_action,
        "reasons": reasons,
        "is_overridden": is_overridden,
        "override_reason": override_reason,
        "features": feats
    }
