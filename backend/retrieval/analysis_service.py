"""Prepare temporal analysis inputs from semantic retrieval results."""

from datetime import date
from typing import Any, Dict, Optional

from backend.temporal.temporal_change import ChangeAnalysisPair, build_change_analysis_pair
from backend.temporal.timeline import SceneTimeline, build_timeline

from .metadata_store import MetadataStore
from .retriever import Retriever
from .pipeline_adapter import PipelineRunner, run_existing_pipeline


class RetrievalAnalysisService:
    """Bridge retrieval and temporal scene selection without running change detection."""

    def __init__(self, retriever: Retriever, metadata: MetadataStore) -> None:
        self.retriever = retriever
        self.metadata = metadata

    def search(
        self,
        query: str,
        *,
        top_k: int = 10,
        reference_date: Optional[date] = None,
        point: Optional[tuple[float, float]] = None,
    ) -> Dict[str, Any]:
        """Run semantic retrieval and return ranked tile results."""

        return self.retriever.search(
            query,
            top_k=top_k,
            reference_date=reference_date,
            point=point,
        )

    def prepare_analysis(
        self,
        tile_id: str,
        *,
        mode: str = "latest",
        before_date: Optional[str] = None,
        after_date: Optional[str] = None,
        minimum_overlap: float = 0.5,
    ) -> Dict[str, Any]:
        """Prepare a temporal handoff for one retrieved tile.

        The returned plan contains source paths and dates only. A caller can
        pass the pair to the existing change-analysis engine in a later phase.
        """

        anchor = self.metadata.get(tile_id)
        timeline = build_timeline(
            anchor,
            self.metadata.all(),
            minimum_overlap=minimum_overlap,
        )
        pair = build_change_analysis_pair(
            timeline,
            mode=mode,
            before_date=before_date,
            after_date=after_date,
        )
        return {
            "tile_id": tile_id,
            "timeline": _timeline_dict(timeline),
            "change_analysis": pair.to_dict(),
        }

    def analyze(
        self,
        tile_id: str,
        *,
        mode: str = "latest",
        before_date: Optional[str] = None,
        after_date: Optional[str] = None,
        location_name: Optional[str] = None,
        runner: Optional[PipelineRunner] = None,
    ) -> Dict[str, Any]:
        """Prepare a pair and optionally execute the existing change pipeline."""

        plan = self.prepare_analysis(
            tile_id,
            mode=mode,
            before_date=before_date,
            after_date=after_date,
        )
        pair = self._pair_from_plan(tile_id, plan)
        change = run_existing_pipeline(pair, location_name=location_name, runner=runner)
        return {**plan, "change": change, "pipeline_invoked": True}

    def _pair_from_plan(self, tile_id: str, plan: Dict[str, Any]):
        before = self.metadata.get(plan["change_analysis"]["before_tile_id"])
        after = self.metadata.get(plan["change_analysis"]["after_tile_id"])
        from backend.temporal.temporal_change import ChangeAnalysisPair

        return ChangeAnalysisPair(before=before, after=after, mode=plan["change_analysis"]["mode"])


def _timeline_dict(timeline: SceneTimeline) -> Dict[str, Any]:
    return {
        "anchor_tile_id": timeline.anchor.tile_id,
        "dates": timeline.dates,
        "scenes": [
            {
                "tile_id": scene.tile_id,
                "scene_id": scene.scene_id,
                "date": scene.date,
                "path": scene.path,
                "bbox": scene.bbox,
            }
            for scene in timeline.scenes
        ],
    }