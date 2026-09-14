"""Focused tests for retrieval-to-temporal analysis preparation."""

from pathlib import Path

from backend.retrieval.analysis_service import RetrievalAnalysisService
from backend.retrieval.metadata_store import MetadataStore, TileMetadata


class FakeRetriever:
    def search(self, query, *, top_k, reference_date=None, point=None):
        return {"query": query, "results": [{"tile_id": "latest", "final_score": 0.9}]}


def scene(tile_id: str, scene_date: str) -> TileMetadata:
    return TileMetadata(
        tile_id=tile_id,
        scene_id="scene-" + tile_id,
        sensor="Sentinel-2",
        date=scene_date,
        bbox=[79.0, 21.0, 79.1, 21.1],
        resolution=10.0,
        cloud_cover=0.2,
        path=str(Path("data/tiles") / (tile_id + ".jpg")),
        embedding_id={"old": 1, "middle": 2, "latest": 3}[tile_id],
    )


def test_search_and_prepare_analysis_handoff(tmp_path):
    metadata = MetadataStore(tmp_path / "tiles.json")
    metadata.add_many(
        [
            scene("old", "2024-01-10"),
            scene("middle", "2024-08-20"),
            scene("latest", "2025-04-18"),
        ]
    )
    service = RetrievalAnalysisService(FakeRetriever(), metadata)

    search = service.search("find new construction", top_k=3)
    plan = service.prepare_analysis("latest")

    assert search["results"][0]["tile_id"] == "latest"
    assert plan["timeline"]["dates"] == ["2024-01-10", "2024-08-20", "2025-04-18"]
    assert plan["change_analysis"]["before_date"] == "2024-08-20"
    assert plan["change_analysis"]["after_date"] == "2025-04-18"


def test_custom_analysis_handoff_preserves_requested_pair(tmp_path):
    metadata = MetadataStore(tmp_path / "tiles.json")
    metadata.add_many(
        [
            scene("old", "2024-01-10"),
            scene("middle", "2024-08-20"),
            scene("latest", "2025-04-18"),
        ]
    )
    service = RetrievalAnalysisService(FakeRetriever(), metadata)

    plan = service.prepare_analysis(
        "latest",
        mode="custom",
        before_date="2024-06-01",
        after_date="2025-01-01",
    )

    assert plan["change_analysis"]["before_tile_id"] == "old"
    assert plan["change_analysis"]["after_tile_id"] == "middle"