"""Focused tests for the existing change-pipeline adapter."""

from backend.retrieval.metadata_store import TileMetadata
from backend.retrieval.pipeline_adapter import run_existing_pipeline
from backend.temporal.temporal_change import ChangeAnalysisPair


def scene(tile_id: str, scene_date: str) -> TileMetadata:
    return TileMetadata(
        tile_id=tile_id,
        scene_id="scene-" + tile_id,
        sensor="Sentinel-2",
        date=scene_date,
        bbox=[79.0, 21.0, 79.1, 21.1],
        resolution=10.0,
        cloud_cover=0.2,
        path=tile_id + ".png",
        embedding_id=1 if tile_id == "before" else 2,
    )


def test_adapter_maps_pair_to_existing_pipeline_contract():
    calls = []

    def fake_runner(**kwargs):
        calls.append(kwargs)
        return {"status": "ok", "change_percent": 4.2}

    pair = ChangeAnalysisPair(scene("before", "2024-01-10"), scene("after", "2025-04-18"), "latest")
    result = run_existing_pipeline(pair, location_name="Nagpur demo", runner=fake_runner)

    assert result["status"] == "ok"
    assert calls == [
        {
            "lat": 21.05,
            "lng": 79.05,
            "location_name": "Nagpur demo",
            "before_date": "2024-01-10",
            "after_date": "2025-04-18",
        }
    ]