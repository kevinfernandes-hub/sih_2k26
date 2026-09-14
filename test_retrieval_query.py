"""Focused tests for query parsing and hybrid retrieval ranking."""

from datetime import date

from backend.retrieval.metadata_store import TileMetadata
from backend.retrieval.query_parser import parse_query
from backend.retrieval.ranking import rank_result


def metadata(tile_date: str = "2025-02-26") -> TileMetadata:
    return TileMetadata(
        tile_id="tile-a",
        scene_id="scene-1",
        sensor="Sentinel-2",
        date=tile_date,
        bbox=[79.05, 21.10, 79.06, 21.11],
        resolution=10.0,
        cloud_cover=0.2,
        path="data/tiles/tile-a.jpg",
        embedding_id=1,
    )


def test_parser_extracts_change_and_temporal_constraints():
    parsed = parse_query("Show vegetation loss during the last year")

    assert parsed.semantic_query == "vegetation loss"
    assert parsed.land_use == "vegetation"
    assert parsed.change_type == "vegetation_loss"
    assert parsed.temporal_preference == "last_year"


def test_parser_extracts_land_use_and_near_feature():
    parsed = parse_query("Find recent construction near major roads")

    assert parsed.date_preference == "recent"
    assert parsed.land_use == "construction"
    assert parsed.change_type == "new_construction"
    assert parsed.near_features == ["roads"]


def test_hybrid_score_combines_components():
    parsed = parse_query("Find recent construction")
    result = rank_result(
        metadata(),
        0.8,
        parsed,
        reference_date=date(2025, 3, 1),
        point=(79.055, 21.105),
    )

    assert result["semantic_score"] == 0.9
    assert result["temporal_score"] > 0.9
    assert result["spatial_score"] == 1.0
    assert 0.0 < result["final_score"] <= 1.0