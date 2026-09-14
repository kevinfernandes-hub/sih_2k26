"""Geographic and chronological timelines for satellite tile metadata."""

from dataclasses import dataclass
from datetime import date
from typing import Iterable, List

from backend.retrieval.metadata_store import TileMetadata


@dataclass(frozen=True)
class SceneTimeline:
    """Chronological imagery available for one geographic tile area."""

    anchor: TileMetadata
    scenes: List[TileMetadata]

    @property
    def dates(self) -> List[str]:
        return [scene.date for scene in self.scenes]


def build_timeline(
    anchor: TileMetadata,
    candidates: Iterable[TileMetadata],
    *,
    minimum_overlap: float = 0.5,
) -> SceneTimeline:
    """Find scenes overlapping the anchor and sort them chronologically."""

    if not 0.0 <= minimum_overlap <= 1.0:
        raise ValueError("minimum_overlap must be between zero and one")
    scenes = {
        candidate.tile_id: candidate
        for candidate in candidates
        if bbox_iou(anchor.bbox, candidate.bbox) >= minimum_overlap
    }
    scenes[anchor.tile_id] = anchor
    ordered = sorted(scenes.values(), key=lambda scene: (date.fromisoformat(scene.date), scene.tile_id))
    return SceneTimeline(anchor=anchor, scenes=ordered)


def bbox_iou(first: List[float], second: List[float]) -> float:
    """Calculate intersection-over-union for WGS84 axis-aligned bounding boxes."""

    if len(first) != 4 or len(second) != 4:
        raise ValueError("Bounding boxes must contain four coordinates")
    first_min_x, first_min_y, first_max_x, first_max_y = first
    second_min_x, second_min_y, second_max_x, second_max_y = second
    intersection_width = max(0.0, min(first_max_x, second_max_x) - max(first_min_x, second_min_x))
    intersection_height = max(0.0, min(first_max_y, second_max_y) - max(first_min_y, second_min_y))
    intersection = intersection_width * intersection_height
    first_area = max(0.0, first_max_x - first_min_x) * max(0.0, first_max_y - first_min_y)
    second_area = max(0.0, second_max_x - second_min_x) * max(0.0, second_max_y - second_min_y)
    union = first_area + second_area - intersection
    return 0.0 if union == 0.0 else intersection / union