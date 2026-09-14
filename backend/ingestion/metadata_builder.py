"""Build retrieval metadata records from generated tiles."""

from pathlib import Path

from backend.retrieval.metadata_store import TileMetadata

from .tile_generator import TileCandidate


def build_tile_metadata(tile: TileCandidate, embedding_id: int, root: Path) -> TileMetadata:
    """Create a portable metadata record using a path relative to the data root."""

    path = tile.path
    try:
        relative_path = path.relative_to(root)
    except ValueError:
        relative_path = path
    return TileMetadata(
        tile_id=tile.tile_id,
        scene_id=tile.scene.scene_id,
        sensor=tile.scene.sensor,
        date=tile.scene.date,
        bbox=tile.bbox,
        resolution=10.0,
        cloud_cover=tile.scene.cloud_cover,
        path=relative_path.as_posix(),
        embedding_id=embedding_id,
        thumbnail=relative_path.as_posix(),
    )