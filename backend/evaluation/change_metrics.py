"""Binary segmentation metrics for change masks."""

from typing import Any

import numpy as np


def binary_metrics(prediction: Any, truth: Any) -> dict[str, float]:
    """Calculate precision, recall, F1, and IoU from binary masks."""

    predicted = np.asarray(prediction).astype(bool)
    actual = np.asarray(truth).astype(bool)
    if predicted.shape != actual.shape:
        raise ValueError("Prediction and truth masks must have identical shapes")
    true_positive = int(np.logical_and(predicted, actual).sum())
    false_positive = int(np.logical_and(predicted, ~actual).sum())
    false_negative = int(np.logical_and(~predicted, actual).sum())
    precision = _ratio(true_positive, true_positive + false_positive)
    recall = _ratio(true_positive, true_positive + false_negative)
    f1 = _ratio(2 * precision * recall, precision + recall)
    iou = _ratio(true_positive, true_positive + false_positive + false_negative)
    return {
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
        "iou": round(iou, 6),
    }


def _ratio(numerator: float, denominator: float) -> float:
    return 0.0 if denominator == 0 else float(numerator) / float(denominator)