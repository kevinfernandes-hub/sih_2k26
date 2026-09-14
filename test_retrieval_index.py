"""Focused tests for the persistent retrieval index and metadata store."""

import numpy as np
import pytest

from backend.retrieval.metadata_store import MetadataStore, TileMetadata
from backend.retrieval.vector_index import VectorIndex


def tile(tile_id: str, embedding_id: int) -> TileMetadata:
    return TileMetadata(
        tile_id=tile_id,
        scene_id="scene-1",
        sensor="Sentinel-2",
        date="2025-02-26",
        bbox=[79.05, 21.10, 79.06, 21.11],
        resolution=10.0,
        cloud_cover=0.2,
        path="data/tiles/" + tile_id + ".jpg",
        embedding_id=embedding_id,
    )


def test_faiss_index_searches_and_reloads(tmp_path):
    metadata = MetadataStore(tmp_path / "tiles.json")
    metadata.add_many([tile("tile-a", 11), tile("tile-b", 12)])
    metadata.save()

    index = VectorIndex(tmp_path / "satellite.index")
    index.add(np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32), [11, 12])
    index.save()

    scores, ids = index.search(np.array([[0.9, 0.1]], dtype=np.float32), top_k=2)
    assert ids[0, 0] == 11
    assert scores[0, 0] > scores[0, 1]

    reloaded = VectorIndex(tmp_path / "satellite.index")
    reloaded.load()
    assert reloaded.ids() == [11, 12]
    assert MetadataStore(tmp_path / "tiles.json").embedding_ids() == [11, 12]


def test_metadata_and_index_reject_duplicate_embedding_ids(tmp_path):
    metadata = MetadataStore(tmp_path / "tiles.json")
    metadata.add(tile("tile-a", 11))
    with pytest.raises(ValueError, match="Embedding ID"):
        metadata.add(tile("tile-b", 11))

    index = VectorIndex(tmp_path / "satellite.index")
    index.add(np.array([[1.0, 0.0]], dtype=np.float32), [11])
    with pytest.raises(ValueError, match="Embedding ID"):
        index.add(np.array([[0.0, 1.0]], dtype=np.float32), [11])