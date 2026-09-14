"""Focused tests for temporal scene linking."""

import pytest

from backend.retrieval.metadata_store import TileMetadata
from backend.temporal import PairingError, bbox_iou, build_change_analysis_pair, build_timeline


def scene(tile_id: str, scene_date: str, bbox=None) -> TileMetadata:
    return TileMetadata(
        tile_id=tile_id,
        scene_id="scene-" + tile_id,
        sensor="Sentinel-2",
        date=scene_date,
        bbox=bbox or [79.0, 21.0, 79.1, 21.1],
        resolution=10.0,
        cloud_cover=0.2,
        path="data/tiles/" + tile_id + ".jpg",
        embedding_id=len(tile_id),
    )


def test_timeline_filters_non_overlapping_scenes_and_sorts_dates():
    anchor = scene("anchor", "2025-04-18")
    timeline = build_timeline(
        anchor,
        [
            scene("before", "2024-01-10"),
            scene("middle", "2024-08-20"),
            scene("outside", "2024-03-01", [80.0, 22.0, 80.1, 22.1]),
        ],
    )

    assert timeline.dates == ["2024-01-10", "2024-08-20", "2025-04-18"]
    assert bbox_iou(anchor.bbox, scene("other", "2025-01-01").bbox) == 1.0


def test_latest_and_custom_pairing():
    timeline = build_timeline(
        scene("latest", "2025-04-18"),
        [scene("old", "2024-01-10"), scene("middle", "2024-08-20")],
    )

    latest = build_change_analysis_pair(timeline)
    custom = build_change_analysis_pair(
        timeline,
        mode="custom",
        before_date="2024-06-01",
        after_date="2025-04-01",
    )

    assert latest.before.tile_id == "middle"
    assert latest.after.tile_id == "latest"
    assert custom.before.tile_id == "old"
    assert custom.after.tile_id == "middle"


def test_pairing_requires_two_scenes():
    timeline = build_timeline(scene("only", "2025-04-18"), [])

    with pytest.raises(PairingError, match="two overlapping scenes"):
        build_change_analysis_pair(timeline)


def test_latest_pairing_skips_duplicate_tiles_on_same_date():
    timeline = build_timeline(
        scene("latest-a", "2025-04-18"),
        [
            scene("before-a", "2024-01-10"),
            scene("before-b", "2024-01-10"),
            scene("latest-b", "2025-04-18"),
        ],
    )

    pair = build_change_analysis_pair(timeline)

    assert pair.before.date == "2024-01-10"
    assert pair.after.date == "2025-04-18"