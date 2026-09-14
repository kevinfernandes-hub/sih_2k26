"""
Nagpur EarthWatch — Officer Feedback Persistence & Training Dataset Store
Phase 5: Human Feedback Logging & Training Dataset Extraction

Persists human officer review decisions (CONFIRMED, FALSE_POSITIVE, NEEDS_REVIEW, Priority)
to serve as genuine ground-truth training data for the adaptive XGBoost model.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from backend.priority_features import extract_priority_features, features_to_vector


FEEDBACK_FILE_PATH = Path("outputs/officer_feedback.json")


def save_officer_feedback(
    case_id: str,
    officer_decision: str,
    officer_priority: Optional[str] = None,
    notes: Optional[str] = None,
    case_data: Optional[Dict[str, Any]] = None,
    yolo_results: Optional[Dict[str, Any]] = None,
    rule_priority: Optional[str] = None
) -> Dict[str, Any]:
    """
    Saves an officer review feedback record to outputs/officer_feedback.json.
    """
    FEEDBACK_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    records = load_all_feedback()
    
    # Extract features for dataset building
    features = extract_priority_features(case_data or {"case_id": case_id}, yolo_results)

    record = {
        "case_id": case_id,
        "officer_decision": officer_decision.upper(),
        "officer_priority": (officer_priority or rule_priority or "HIGH").upper(),
        "rule_priority": (rule_priority or "HIGH").upper(),
        "notes": notes or "",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "features": features
    }

    # Upsert by case_id
    existing_idx = next((i for i, r in enumerate(records) if r.get("case_id") == case_id), -1)
    if existing_idx >= 0:
        records[existing_idx] = record
    else:
        records.append(record)

    with open(FEEDBACK_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    return {
        "status": "SUCCESS",
        "case_id": case_id,
        "total_feedback_records": len(records),
        "record": record
    }


def load_all_feedback() -> List[Dict[str, Any]]:
    """
    Loads all saved officer feedback records. Returns empty list if missing.
    """
    if not FEEDBACK_FILE_PATH.exists():
        return []
    try:
        with open(FEEDBACK_FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def get_training_dataset() -> Tuple[List[List[float]], List[str], List[Dict[str, Any]]]:
    """
    Extracts feature vectors (X) and officer target labels (y) from genuine feedback logs.
    """
    records = load_all_feedback()
    X: List[List[float]] = []
    y: List[str] = []

    for r in records:
        feats = r.get("features", {})
        vec = features_to_vector(feats)
        label = r.get("officer_priority") or r.get("rule_priority") or "HIGH"
        X.append(vec)
        y.append(label)

    return X, y, records
