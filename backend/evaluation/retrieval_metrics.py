"""Recall metrics for semantic retrieval benchmarks."""

from typing import Iterable, Mapping, Sequence


def recall_at_k(retrieved: Sequence[str], relevant: Iterable[str], k: int) -> float:
    """Return binary query recall at ``k`` for a set of relevant tile IDs."""

    if k < 1:
        raise ValueError("k must be greater than zero")
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    return float(bool(set(retrieved[:k]).intersection(relevant_set)))


def evaluate_retrieval(
    search_fn,
    labels: Mapping[str, Iterable[str]],
    ks: Sequence[int] = (1, 5, 10),
) -> dict[str, object]:
    """Evaluate labeled queries without inventing labels or scores."""

    if not labels:
        return {"queries": 0, "recall": None, "mean_recall": None}
    values = {}
    for k in ks:
        scores = []
        for query, relevant in labels.items():
            result = search_fn(query, top_k=k)
            retrieved = [item["tile_id"] for item in result.get("results", [])]
            scores.append(recall_at_k(retrieved, relevant, k))
        values[f"recall_at_{k}"] = round(sum(scores) / len(scores), 6)
    values["queries"] = len(labels)
    values["mean_recall"] = round(
        sum(float(values[f"recall_at_{k}"]) for k in ks) / len(ks), 6
    )
    return values