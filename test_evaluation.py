"""Focused tests for measured evaluation metrics."""

import numpy as np

from backend.evaluation.change_metrics import binary_metrics
from backend.evaluation.benchmark import run_benchmark
from backend.evaluation.retrieval_metrics import evaluate_retrieval, recall_at_k


def test_retrieval_recall():
    assert recall_at_k(["a", "b"], ["b"], 2) == 1.0
    result = evaluate_retrieval(
        lambda query, top_k: {"results": [{"tile_id": "a"}, {"tile_id": "b"}]},
        {"construction": ["b"]},
    )
    assert result["recall_at_1"] == 0.0
    assert result["recall_at_5"] == 1.0


def test_change_metrics():
    result = binary_metrics(
        np.array([[1, 1], [0, 0]]),
        np.array([[1, 0], [0, 1]]),
    )
    assert result == {"precision": 0.5, "recall": 0.5, "f1": 0.5, "iou": 0.333333}


def test_benchmark_execution_reports_unlabeled_metrics_as_null(monkeypatch, tmp_path):
    metadata_path = tmp_path / "tiles.json"
    metadata_path.write_text("[]", encoding="utf-8")
    monkeypatch.setenv("RETRIEVAL_METADATA_PATH", str(metadata_path))
    monkeypatch.setenv("RETRIEVAL_INDEX_PATH", str(tmp_path / "missing.index"))
    monkeypatch.setenv("RETRIEVAL_MODEL_PATH", str(tmp_path / "missing.pt"))

    report = run_benchmark()

    assert report["retrieval"]["mean_recall"] is None
    assert report["temporal_dataset"]["geographic_areas"] == 0