"""Incremental offline ingestion into the local tile index."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from backend.retrieval.encoder import EmbeddingEncoder
from backend.retrieval.metadata_store import MetadataStore
from backend.retrieval.vector_index import VectorIndex

from .metadata_builder import build_tile_metadata
from .scene_scanner import scan_scenes
from .tile_generator import generate_tiles


@dataclass(frozen=True)
class IngestionResult:
    scenes_seen: int
    scenes_added: int
    tiles_added: int


class IncrementalIngester:
    """Skip indexed scenes and append only new tile embeddings."""

    def __init__(self, data_dir: Path, encoder: EmbeddingEncoder, tile_size: int = 512, overlap: float = 0.0) -> None:
        self.data_dir = Path(data_dir)
        self.encoder = encoder
        self.tile_size = tile_size
        self.overlap = overlap
        self.metadata = MetadataStore(self.data_dir / "metadata" / "tiles.json")
        self.index = VectorIndex(self.data_dir / "indexes" / "satellite.index")
        self.manifest_path = self.data_dir / "manifests" / "scenes.json"
        self.tile_dir = self.data_dir / "tiles"

    def ingest(self, input_dir: Path) -> IngestionResult:
        scenes = scan_scenes(input_dir)
        indexed_scene_ids = set(self._manifest().get("indexed_scenes", []))
        new_scenes = [scene for scene in scenes if scene.scene_id not in indexed_scene_ids]
        candidates = []
        for scene in new_scenes:
            candidates.extend(generate_tiles(scene, self.tile_dir, self.tile_size, self.overlap))
        if not candidates:
            return IngestionResult(len(scenes), 0, 0)

        image_paths = [candidate.path for candidate in candidates]
        embeddings = np.asarray(self.encoder.encode_images(image_paths), dtype=np.float32)
        first_id = max(self.metadata.embedding_ids(), default=0) + 1
        records = [
            build_tile_metadata(candidate, first_id + offset, self.data_dir)
            for offset, candidate in enumerate(candidates)
        ]
        if self.index.path.exists():
            self.index.load()
        self.index.add(embeddings, [record.embedding_id for record in records])
        self.metadata.add_many(records)
        self.index.save()
        self.metadata.save()
        self._save_manifest(
            indexed_scene_ids | {scene.scene_id for scene in new_scenes},
            records,
        )
        return IngestionResult(len(scenes), len(new_scenes), len(records))

    def _manifest(self) -> Dict[str, Any]:
        if not self.manifest_path.exists():
            return {"indexed_scenes": []}
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {"indexed_scenes": []}

    def _save_manifest(self, scene_ids: set[str], records) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        existing = self._manifest()
        scene_records = dict(existing.get("scenes", {}))
        for record in records:
            scene = scene_records.setdefault(
                record.scene_id,
                {
                    "scene_id": record.scene_id,
                    "sensor": record.sensor,
                    "date": record.date,
                    "bbox": record.bbox,
                    "resolution": record.resolution,
                    "cloud_cover": record.cloud_cover,
                    "tiles": [],
                },
            )
            if record.tile_id not in scene["tiles"]:
                scene["tiles"].append(record.tile_id)
        self.manifest_path.write_text(
            json.dumps(
                {"indexed_scenes": sorted(scene_ids), "scenes": scene_records},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )