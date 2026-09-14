"""Focused tests for incremental offline scene ingestion."""

import numpy as np
from PIL import Image

from backend.ingestion.incremental_ingest import IncrementalIngester


class FakeEncoder:
    def encode_images(self, images):
        return np.array([[1.0, float(index + 1)] for index, _ in enumerate(images)], dtype=np.float32)


def write_scene(directory, scene_id, scene_date):
    image_path = directory / (scene_id + ".png")
    Image.new("RGB", (4, 4), color=(100, 120, 140)).save(image_path)
    image_path.with_suffix(".json").write_text(
        '{"scene_id": "' + scene_id + '", "date": "' + scene_date + '", '
        '"sensor": "Sentinel-2", "bbox": [79.0, 21.0, 79.1, 21.1], "cloud_cover": 0.2}',
        encoding="utf-8",
    )


def test_ingester_adds_new_scenes_and_skips_existing(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    write_scene(input_dir, "S2A_20250101", "2025-01-01")
    ingester = IncrementalIngester(tmp_path / "data", FakeEncoder(), tile_size=4)

    first = ingester.ingest(input_dir)
    second = ingester.ingest(input_dir)

    assert first.scenes_added == 1
    assert first.tiles_added == 1
    assert second.scenes_added == 0
    assert second.tiles_added == 0
    assert len(ingester.metadata.all()) == 1
    assert ingester.index.size == 1