"""
Nagpur EarthWatch — Stage 5B Explanation Engine Unit Test
Tests Gemini/Grok explanation layer and deterministic fallback.
"""

from backend.priority_engine import evaluate_rule_priority
from backend.explanation_engine import generate_officer_explanation, generate_deterministic_fallback


def run_tests():
    print("=" * 70)
    print("Nagpur EarthWatch — Phase 5B Explanation Engine Test")
    print("=" * 70)

    sample_case = {
        "case_id": "CASE #NGP-MIHAN-BLDG-001",
        "location_name": "AIIMS Hospital Complex (Phase II Expansion)",
        "ward": "36",
        "zone": "Laxmi Nagar",
        "before_date": "2019-01-31",
        "after_date": "2025-01-30",
        "change_type": "NEW",
        "urban_growth_risk": "HIGH"
    }

    rule_res = evaluate_rule_priority(sample_case)

    # 1. Test Deterministic Fallback directly
    fallback = generate_deterministic_fallback(sample_case, rule_res)
    print("[1] Deterministic Fallback Output:")
    print(f"    - What Happened: {fallback['what_happened']}")
    print(f"    - Action:        {fallback['recommended_action']}")
    print(f"    - Source:        {fallback['explanation_source']}")
    print("    - Reasons:")
    for r in fallback['why_flagged']:
        print(f"      * {r}")
    print("    - Officer Checklist:")
    for v in fallback['what_officer_should_verify']:
        print(f"      [x] {v}")

    # 2. Test Main Explanation Function (Grok / Gemini API or Fallback)
    exp = generate_officer_explanation(sample_case, rule_res)
    print("\n[2] Explanation Layer Output:")
    print(f"    - Source:  {exp.get('explanation_source')}")
    print(f"    - Engine:  {exp.get('engine_note', 'Active LLM API')}")
    print(f"    - Summary: {exp.get('evidence_summary')}")

    print("=" * 70)
    print("Phase 5B Explanation Engine Test Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
