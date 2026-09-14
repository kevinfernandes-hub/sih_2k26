"""
Nagpur EarthWatch — Stage 5A Priority Engine & XGBoost Unit Test
Tests feature extraction, rule prioritization, overrides, officer feedback persistence,
and XGBoost adaptive model fallback.
"""

from backend.priority_features import extract_priority_features, features_to_vector
from backend.priority_engine import evaluate_rule_priority
from backend.priority_training import save_officer_feedback, load_all_feedback, get_training_dataset
from backend.priority_xgboost import evaluate_xgboost_priority


def run_tests():
    print("=" * 70)
    print("Nagpur EarthWatch — Phase 5A Priority Engine & Feedback Test")
    print("=" * 70)

    # 1. Test Feature Extraction
    sample_case = {
        "case_id": "CASE #NGP-MIHAN-BLDG-001",
        "change_pixel_area": 1812.0,
        "change_pct": 7.06,
        "change_type": "NEW",
        "ward": "36",
        "zone": "Laxmi Nagar",
        "urban_growth_risk": "HIGH"
    }

    sample_yolo = {
        "summary": {"total_change_pixel_area": 1812.0, "new_count": 1, "top_yolo_confidence": 0.68},
        "detections": [{"building_id": "BLDG-001", "status": "NEW", "after_confidence": 0.68, "iou": 0.0}]
    }

    feats = extract_priority_features(sample_case, sample_yolo)
    vec = features_to_vector(feats)
    print("[1] Feature Extraction:")
    print(f"    - Change Area: {feats['change_pixel_area']} px")
    print(f"    - YOLO Conf:   {feats['yolo_confidence']}")
    print(f"    - Change Code: {feats['change_type_code']} ({feats['change_type_raw']})")
    print(f"    - Vector Dim:  {len(vec)} features")

    # 2. Test Rule-Based Engine
    rule_res = evaluate_rule_priority(sample_case, sample_yolo)
    print("\n[2] Rule-Based Priority Engine Output:")
    print(f"    - Priority:           {rule_res['priority']}")
    print(f"    - Score:              {rule_res['priority_score']}/100")
    print(f"    - Evidence Strength:  {rule_res['evidence_strength']}")
    print(f"    - Recommended Action: {rule_res['recommended_action']}")
    print(f"    - Reasons Count:      {len(rule_res['reasons'])}")
    for r in rule_res['reasons']:
        print(f"      * {r}")

    # 3. Test Officer Feedback Persistence
    fb_res = save_officer_feedback(
        case_id="CASE #NGP-MIHAN-BLDG-001",
        officer_decision="CONFIRMED",
        officer_priority="HIGH",
        notes="Verified site on ground. Structure is new.",
        case_data=sample_case,
        rule_priority=rule_res['priority']
    )
    print("\n[3] Officer Feedback Persistence:")
    print(f"    - Save Status:    {fb_res['status']}")
    print(f"    - Total Feedback: {fb_res['total_feedback_records']} records")

    # 4. Test XGBoost Adaptive Model
    xgb_res = evaluate_xgboost_priority(feats)
    print("\n[4] XGBoost Adaptive Model Status:")
    print(f"    - Model Status: {xgb_res['model_status']}")
    print(f"    - Message:      {xgb_res['message']}")
    print(f"    - Fallback:     {xgb_res['fallback_to_rules']}")
    print(f"    - Samples:      {xgb_res['training_dataset_size']}")

    print("=" * 70)
    print("Phase 5A Priority Engine Test Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
