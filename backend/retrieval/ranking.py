"""Configurable hybrid scoring for semantic satellite retrieval."""

from dataclasses import dataclass
from datetime import date, timedelta
from math import hypot
from typing import Any, Dict, Optional, Sequence

from .metadata_store import TileMetadata
from .query_parser import RetrievalQuery


@dataclass(frozen=True)
class RankingWeights:
    semantic: float = 0.60
    temporal: float = 0.20
    spatial: float = 0.10
    metadata: float = 0.10

    def __post_init__(self) -> None:
        values = (self.semantic, self.temporal, self.spatial, self.metadata)
        if any(value < 0 for value in values) or abs(sum(values) - 1.0) > 1e-6:
            raise ValueError("Ranking weights must be non-negative and sum to 1")


def rank_result(
    metadata: TileMetadata,
    semantic_score: float,
    query: RetrievalQuery,
    *,
    weights: RankingWeights = RankingWeights(),
    reference_date: Optional[date] = None,
    point: Optional[tuple[float, float]] = None,
) -> Dict[str, Any]:
    """Return interpretable component scores and a weighted final score."""

    semantic = _clamp((semantic_score + 1.0) / 2.0)
    temporal = temporal_score(metadata, query, reference_date)
    spatial = spatial_score(metadata, point)
    metadata_score = metadata_quality_score(metadata)
    final = (
        weights.semantic * semantic
        + weights.temporal * temporal
        + weights.spatial * spatial
        + weights.metadata * metadata_score
    )
    return {
        "tile_id": metadata.tile_id,
        "scene_id": metadata.scene_id,
        "date": metadata.date,
        "bbox": metadata.bbox,
        "path": metadata.path,
        "thumbnail": metadata.thumbnail,
        "semantic_score": round(semantic, 6),
        "temporal_score": round(temporal, 6),
        "spatial_score": round(spatial, 6),
        "metadata_score": round(metadata_score, 6),
        "final_score": round(final, 6),
    }


def temporal_score(metadata: TileMetadata, query: RetrievalQuery, reference_date: Optional[date]) -> float:
    if not query.date_preference and not query.temporal_preference:
        return 1.0
    anchor = reference_date or date.today()
    tile_date = date.fromisoformat(metadata.date)
    age_days = max(0, (anchor - tile_date).days)
    if query.temporal_preference == "last_year":
        return 1.0 if age_days <= 365 else 0.0
    if query.temporal_preference == "last_month":
        return 1.0 if age_days <= 31 else 0.0
    return _clamp(1.0 - age_days / 3650.0)


def spatial_score(metadata: TileMetadata, point: Optional[tuple[float, float]]) -> float:
    if point is None:
        return 1.0
    longitude, latitude = point
    min_lng, min_lat, max_lng, max_lat = metadata.bbox
    if min_lng <= longitude <= max_lng and min_lat <= latitude <= max_lat:
        return 1.0
    center_lng = (min_lng + max_lng) / 2.0
    center_lat = (min_lat + max_lat) / 2.0
    return _clamp(1.0 - hypot(longitude - center_lng, latitude - center_lat) / 0.25)


def metadata_quality_score(metadata: TileMetadata) -> float:
    if metadata.cloud_cover is None:
        return 0.5
    return _clamp(1.0 - metadata.cloud_cover / 100.0)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))