"""Focused tests for retrieval API request handling and offline status."""

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.retrieval import api


def test_index_status_reads_local_metadata(monkeypatch, tmp_path):
    metadata_path = tmp_path / "tiles.json"
    metadata_path.write_text(
        json.dumps(
            [
                {
                    "tile_id": "tile-a",
                    "scene_id": "scene-a",
                    "sensor": "Sentinel-2",
                    "date": "2025-02-26",
                    "bbox": [79.0, 21.0, 79.1, 21.1],
                    "resolution": 10,
                    "cloud_cover": 0.2,
                    "path": "tile-a.jpg",
                    "embedding_id": 1,
                }
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("RETRIEVAL_METADATA_PATH", str(metadata_path))
    monkeypatch.setenv("RETRIEVAL_INDEX_PATH", str(tmp_path / "missing.index"))
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)

    response = client.get("/api/retrieval/index/status")

    assert response.status_code == 200
    assert response.json()["indexed_tiles"] == 1
    assert response.json()["geographic_areas"] == 1
    assert response.json()["offline_mode"] is True


def test_search_reports_unavailable_local_model(monkeypatch, tmp_path):
    monkeypatch.setenv("RETRIEVAL_METADATA_PATH", str(tmp_path / "tiles.json"))
    monkeypatch.setenv("RETRIEVAL_INDEX_PATH", str(tmp_path / "missing.index"))
    monkeypatch.setenv("RETRIEVAL_MODEL_PATH", str(tmp_path / "missing.pt"))
    api._SERVICE = None
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)

    response = client.post("/api/retrieval/search", json={"query": "new construction"})

    assert response.status_code == 503
    assert "checkpoint" in response.json()["detail"]


def test_ingest_rejects_missing_scene_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("RETRIEVAL_DATA_DIR", str(tmp_path / "data"))
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)

    response = client.post("/api/retrieval/ingest", json={"input_dir": str(tmp_path / "missing")})

    assert response.status_code == 400
    assert "Input scene directory" in response.json()["detail"]