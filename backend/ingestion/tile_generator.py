"""Deterministic image tiling for staged satellite scenes."""

from dataclasses import dataclass
from pathlib import Path
from typing import List

from PIL import Image

from .scene_scanner import SceneRecord


@dataclass(frozen=True)
class TileCandidate:
    tile_id: str
    scene: SceneRecord
    path: Path
    bbox: List[float]


def generate_tiles(
    scene: SceneRecord,
    output_dir: Path,
    tile_size: int = 512,
    overlap: float = 0.0,
) -> List[TileCandidate]:
    """Create deterministic PNG tiles and map each tile to a scene bbox."""

    if tile_size < 1:
        raise ValueError("tile_size must be greater than zero")
    if not 0.0 <= overlap < 1.0:
        raise ValueError("overlap must be between zero inclusive and one exclusive")
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates: List[TileCandidate] = []
    with Image.open(scene.path) as image:
        image = image.convert("RGB")
        width, height = image.size
        stride = max(1, int(round(tile_size * (1.0 - overlap))))
        columns = _starts(width, tile_size, stride)
        rows = _starts(height, tile_size, stride)
        for row, top in enumerate(rows):
            for column, left in enumerate(columns):
                right = min(width, left + tile_size)
                bottom = min(height, top + tile_size)
                tile_id = f"{scene.scene_id}_{row:03d}_{column:03d}"
                tile_path = output_dir / (tile_id + ".png")
                image.crop((left, top, right, bottom)).save(tile_path)
                candidates.append(
                    TileCandidate(
                        tile_id=tile_id,
                        scene=scene,
                        path=tile_path,
                        bbox=_tile_bbox(scene.bbox, left / width, top / height, right / width, bottom / height),
                    )
                )
    return candidates


def _starts(length: int, tile_size: int, stride: int) -> List[int]:
    if length <= tile_size:
        return [0]
    starts = list(range(0, length - tile_size + 1, stride))
    final_start = length - tile_size
    if starts[-1] != final_start:
        starts.append(final_start)
    return starts


def _tile_bbox(bbox: List[float], left: float, top: float, right: float, bottom: float) -> List[float]:
    min_lng, min_lat, max_lng, max_lat = bbox
    return [
        min_lng + (max_lng - min_lng) * left,
        min_lat + (max_lat - min_lat) * top,
        min_lng + (max_lng - min_lng) * right,
        min_lat + (max_lat - min_lat) * bottom,
    ]