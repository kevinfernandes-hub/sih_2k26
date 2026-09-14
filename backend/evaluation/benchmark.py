"""Measured benchmark command for the local retrieval index."""

import argparse
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict

from backend.retrieval.api import _paths, _service, retrieval_index_status
from backend.retrieval.metadata_store import MetadataStore, group_overlapping_areas
from backend.retrieval.vector_index import VectorIndex

from .retrieval_metrics import evaluate_retrieval


def run_benchmark(
    labels_path: Path | None = None,
    *,
    build_input: Path | None = None,
    incremental_input: Path | None = None,
    queries_path: Path | None = None,
) -> Dict[str, Any]:
    """Return measured index statistics and optional labeled/timing metrics."""

    status = retrieval_index_status()
    report: Dict[str, Any] = {
        "index_status": status,
        "retrieval": {
            "queries": 0,
            "recall_at_1": None,
            "recall_at_5": None,
            "recall_at_10": None,
            "mean_recall": None,
        },
        "latency_ms": {
            "semantic_query": None,
            "faiss_search": None,
            "end_to_end": None,
        },
        "timing": {"index_build_seconds": None, "incremental_ingest_seconds": None},
        "temporal_dataset": _temporal_dataset(status),
    }

    if build_input is not None:
        report["timing"]["index_build_seconds"] = _measure_ingest(build_input, fresh=True)
    if incremental_input is not None:
        report["timing"]["incremental_ingest_seconds"] = _measure_ingest(incremental_input, fresh=False)
    if labels_path is None:
        if queries_path is not None:
            report["latency_ms"] = _measure_queries(queries_path)
        return report

    labels = json.loads(labels_path.read_text(encoding="utf-8"))
    if isinstance(labels, list):
        labels = {item["query"]: item["relevant_tile_ids"] for item in labels}
    if not isinstance(labels, dict):
        raise ValueError("Retrieval labels must be a JSON object or list of labeled queries")
    service = _service()
    retriever = service.retriever
    end_to_end_timings = []
    semantic_timings = []
    faiss_timings = []

    def timed_search(query: str, top_k: int):
        started = time.perf_counter()
        parsed = retriever.parser.parse(query)
        semantic_start = time.perf_counter()
        query_vector = retriever.encoder.encode_text([parsed.semantic_query])
        semantic_timings.append((time.perf_counter() - semantic_start) * 1000.0)
        faiss_start = time.perf_counter()
        scores, ids = service.index.search(query_vector, top_k=top_k)
        faiss_timings.append((time.perf_counter() - faiss_start) * 1000.0)
        result = service.search(query, top_k=top_k)
        end_to_end_timings.append((time.perf_counter() - started) * 1000.0)
        return result

    report["retrieval"] = evaluate_retrieval(timed_search, labels)
    report["latency_ms"] = {
        "semantic_query": _average(semantic_timings),
        "faiss_search": _average(faiss_timings),
        "end_to_end": _average(end_to_end_timings),
    }
    return report


def _measure_queries(queries_path: Path) -> Dict[str, float | None]:
    queries = json.loads(queries_path.read_text(encoding="utf-8"))
    if not isinstance(queries, list) or not all(isinstance(query, str) for query in queries):
        raise ValueError("Query benchmark file must be a JSON list of strings")
    service = _service()
    retriever = service.retriever
    semantic_timings = []
    faiss_timings = []
    end_to_end_timings = []
    for query in queries:
        parsed = retriever.parser.parse(query)
        semantic_start = time.perf_counter()
        query_vector = retriever.encoder.encode_text([parsed.semantic_query])
        semantic_timings.append((time.perf_counter() - semantic_start) * 1000.0)
        faiss_start = time.perf_counter()
        retriever.index.search(query_vector, top_k=10)
        faiss_timings.append((time.perf_counter() - faiss_start) * 1000.0)
        end_to_end_start = time.perf_counter()
        service.search(query, top_k=10)
        end_to_end_timings.append((time.perf_counter() - end_to_end_start) * 1000.0)
    return {
        "semantic_query": _average(semantic_timings),
        "faiss_search": _average(faiss_timings),
        "end_to_end": _average(end_to_end_timings),
    }


def _average(values):
    return round(sum(values) / len(values), 3) if values else None


def _temporal_dataset(status: Dict[str, Any]) -> Dict[str, Any]:
    metadata = MetadataStore(Path(status["metadata_path"]))
    areas = group_overlapping_areas(metadata.all())
    temporal_pairs = sum(
        max(0, len({record.date for record in area}) - 1)
        for area in areas
    )
    return {
        "geographic_areas": len(areas),
        "temporal_pairs": temporal_pairs,
        "date_range": status["date_range"],
    }


def _measure_ingest(input_dir: Path, *, fresh: bool) -> float | None:
    """Measure ingestion only when explicitly requested; never alter the live index."""

    from backend.ingestion.incremental_ingest import IncrementalIngester
    from backend.retrieval.encoder import RemoteCLIPConfig, RemoteCLIPEncoder
    import tempfile
    import shutil

    paths = _paths()
    encoder = RemoteCLIPEncoder(RemoteCLIPConfig(checkpoint_path=paths["model"]))
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary) / "data"
        if not fresh:
            source_data = paths["metadata"].parents[1]
            if source_data.exists():
                shutil.copytree(source_data, target, dirs_exist_ok=True)
        started = time.perf_counter()
        IncrementalIngester(target, encoder).ingest(input_dir)
        return round(time.perf_counter() - started, 3)


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark local semantic retrieval")
    parser.add_argument("--labels", type=Path, default=None, help="JSON mapping of query to relevant tile IDs")
    parser.add_argument("--build-input", type=Path, default=None, help="Optional source directory for isolated build timing")
    parser.add_argument("--incremental-input", type=Path, default=None, help="Optional source directory for isolated incremental timing")
    parser.add_argument("--queries", type=Path, default=None, help="JSON list of unlabeled queries for latency measurement")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    report = run_benchmark(
        args.labels,
        build_input=args.build_input,
        incremental_input=args.incremental_input,
        queries_path=args.queries,
    )
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()