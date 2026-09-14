"""
Nagpur EarthWatch — XGBoost Adaptive Priority Model
Phase 5: Machine Learning Priority Classification from Human Officer Feedback

Uses XGBoost to learn municipal priority patterns from genuine officer-reviewed cases.
Safely falls back to Rule-Based Engine when labelled training examples are < 10.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from backend.priority_features import features_to_vector
from backend.priority_training import get_training_dataset


CLASS_NAMES = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "NEEDS_REVIEW"]
FEATURE_NAMES = [
    "change_pixel_area",
    "change_pct",
    "new_buildings_count",
    "expanded_buildings_count",
    "yolo_confidence",
    "verification_score",
    "iou",
    "ssim_divergence",
    "edge_emergence",
    "time_delta_days",
    "change_type_code",
    "sensitivity_score",
    "image_quality_code"
]

MIN_REQUIRED_TRAINING_CASES = 10


def evaluate_xgboost_priority(
    case_features: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates XGBoost model prediction.
    If labelled cases < 10, returns ADAPTIVE_MODEL_NOT_READY and triggers rule-based fallback.
    """
    X, y, records = get_training_dataset()
    n_samples = len(records)

    if n_samples < MIN_REQUIRED_TRAINING_CASES:
        return {
            "model_status": "ADAPTIVE_MODEL_NOT_READY",
            "message": f"Adaptive Model: Not Ready (Insufficient labelled officer feedback. Requires {MIN_REQUIRED_TRAINING_CASES} cases, found {n_samples})",
            "fallback_to_rules": True,
            "training_dataset_size": n_samples,
            "min_required_cases": MIN_REQUIRED_TRAINING_CASES,
            "model_version": "v0.1-rule-fallback",
            "prediction": None,
            "prediction_confidence": None,
            "feature_importances": {name: round(1.0 / len(FEATURE_NAMES), 3) for name in FEATURE_NAMES},
            "metrics": {
                "accuracy": None,
                "macro_f1": None,
                "note": "Evaluation unavailable — insufficient labelled data"
            }
        }

    # Attempt XGBoost training if dataset >= 10
    try:
        from xgboost import XGBClassifier
        from sklearn.preprocessing import LabelEncoder
        from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

        le = LabelEncoder()
        y_enc = le.fit_transform(y)

        model = XGBClassifier(
            n_estimators=50,
            max_depth=3,
            learning_rate=0.1,
            eval_metric="mlogloss",
            random_state=42
        )
        model.fit(X, y_enc)

        # Predict input case
        input_vec = np.array([features_to_vector(case_features)])
        pred_enc = model.predict(input_vec)[0]
        pred_probs = model.predict_proba(input_vec)[0]
        pred_label = le.inverse_transform([pred_enc])[0]
        confidence_prob = float(np.max(pred_probs))

        # Calculate metrics on training set
        train_preds = model.predict(X)
        acc = float(accuracy_score(y_enc, train_preds))
        f1 = float(f1_score(y_enc, train_preds, average="macro", zero_division=0))
        prec = float(precision_score(y_enc, train_preds, average="macro", zero_division=0))
        rec = float(recall_score(y_enc, train_preds, average="macro", zero_division=0))

        # Feature importances
        imp_vals = model.feature_importances_
        feature_importances = {
            name: round(float(imp_vals[i]), 3) for i, name in enumerate(FEATURE_NAMES)
        }

        return {
            "model_status": "ACTIVE",
            "message": "XGBoost Adaptive Priority Model Active (Trained on Genuine Officer Feedback)",
            "fallback_to_rules": False,
            "training_dataset_size": n_samples,
            "model_version": "v1.0-xgboost-trained",
            "prediction": pred_label,
            "prediction_confidence": round(confidence_prob, 4),
            "feature_importances": feature_importances,
            "metrics": {
                "accuracy": round(acc, 4),
                "macro_f1": round(f1, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4)
            }
        }
    except Exception as err:
        return {
            "model_status": "ERROR_FALLBACK",
            "message": f"XGBoost Model Error: {str(err)}. Falling back to Rule-Based Engine.",
            "fallback_to_rules": True,
            "training_dataset_size": n_samples,
            "model_version": "v0.1-rule-fallback",
            "prediction": None,
            "prediction_confidence": None,
            "feature_importances": {name: round(1.0 / len(FEATURE_NAMES), 3) for name in FEATURE_NAMES},
            "metrics": {
                "accuracy": None,
                "macro_f1": None,
                "note": f"Error: {str(err)}"
            }
        }
