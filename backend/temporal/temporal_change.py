"""Pipeline-neutral temporal change analysis requests."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from backend.retrieval.metadata_store import TileMetadata

from .scene_pairing import pair_scenes
from .timeline import SceneTimeline


@dataclass(frozen=True)
class ChangeAnalysisPair:
    """The selected inputs that can be passed to the existing change engine."""

    before: TileMetadata
    after: TileMetadata
    mode: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "before_tile_id": self.before.tile_id,
            "before_date": self.before.date,
            "before_path": self.before.path,
            "after_tile_id": self.after.tile_id,
            "after_date": self.after.date,
            "after_path": self.after.path,
            "bbox": self.after.bbox,
            "mode": self.mode,
        }


def build_change_analysis_pair(
    timeline: SceneTimeline,
    *,
    mode: str = "latest",
    before_date: Optional[str] = None,
    after_date: Optional[str] = None,
) -> ChangeAnalysisPair:
    """Select temporal inputs without invoking or modifying change detection."""

    before, after = pair_scenes(
        timeline,
        mode=mode,
        before_date=before_date,
        after_date=after_date,
    )
    return ChangeAnalysisPair(before=before, after=after, mode=mode)