"""Adapter from retrieved temporal pairs to the existing change pipeline."""

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Dict, Optional, Tuple

from backend.temporal.temporal_change import ChangeAnalysisPair


PipelineRunner = Callable[..., Dict[str, Any]]


@dataclass(frozen=True)
class PipelineInput:
    """Location and dates accepted by ``run_analysis_pipeline``."""

    latitude: float
    longitude: float
    location_name: str
    before_date: str
    after_date: str


def pipeline_input_from_pair(pair: ChangeAnalysisPair, location_name: Optional[str] = None) -> PipelineInput:
    """Convert a tile pair into the existing pipeline's public arguments."""

    min_lng, min_lat, max_lng, max_lat = pair.after.bbox
    return PipelineInput(
        latitude=(min_lat + max_lat) / 2.0,
        longitude=(min_lng + max_lng) / 2.0,
        location_name=location_name or pair.after.tile_id,
        before_date=pair.before.date,
        after_date=pair.after.date,
    )


def run_existing_pipeline(
    pair: ChangeAnalysisPair,
    *,
    location_name: Optional[str] = None,
    runner: Optional[PipelineRunner] = None,
) -> Dict[str, Any]:
    """Invoke the existing pipeline through an injectable adapter boundary."""

    if runner is None:
        from backend.pipeline import run_analysis_pipeline

        runner = run_analysis_pipeline
    pipeline_input = pipeline_input_from_pair(pair, location_name)
    return runner(
        lat=pipeline_input.latitude,
        lng=pipeline_input.longitude,
        location_name=pipeline_input.location_name,
        before_date=pipeline_input.before_date,
        after_date=pipeline_input.after_date,
    )