"""Persistent metadata records for indexed satellite tiles."""

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class TileMetadata:
    """Metadata required to identify and locate one indexed tile."""

    tile_id: str
    scene_id: str
    sensor: str
    date: str
    bbox: List[float]
    resolution: float
    cloud_cover: Optional[float]
    path: str
    embedding_id: int
    thumbnail: Optional[str] = None

    def __post_init__(self) -> None:
        if len(self.bbox) != 4:
            raise ValueError("TileMetadata bbox must contain four coordinates")
        date.fromisoformat(self.date)
        if self.embedding_id < 0:
            raise ValueError("TileMetadata embedding_id must be non-negative")


class MetadataStore:
    """JSON persistence for tile metadata keyed by tile and embedding IDs."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._records: Dict[str, TileMetadata] = {}
        self._load()

    def add(self, record: TileMetadata) -> None:
        existing = self._records.get(record.tile_id)
        if existing is not None and existing != record:
            raise ValueError("Tile ID already exists with different metadata: " + record.tile_id)
        for other in self._records.values():
            if other.tile_id != record.tile_id and other.embedding_id == record.embedding_id:
                raise ValueError("Embedding ID already belongs to another tile")
        self._records[record.tile_id] = record

    def add_many(self, records: Iterable[TileMetadata]) -> None:
        for record in records:
            self.add(record)

    def get(self, tile_id: str) -> TileMetadata:
        try:
            return self._records[tile_id]
        except KeyError as exc:
            raise KeyError("Unknown tile ID: " + tile_id) from exc

    def get_by_embedding_id(self, embedding_id: int) -> TileMetadata:
        for record in self._records.values():
            if record.embedding_id == embedding_id:
                return record
        raise KeyError("Unknown embedding ID: " + str(embedding_id))

    def all(self) -> List[TileMetadata]:
        return sorted(self._records.values(), key=lambda record: record.embedding_id)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [asdict(record) for record in self.all()]
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary_path.replace(self.path)

    def embedding_ids(self) -> List[int]:
        return [record.embedding_id for record in self.all()]

    def _load(self) -> None:
        if not self.path.exists():
            return
        payload: Any = json.loads(self.path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = payload.get("tiles", [])
        if not isinstance(payload, list):
            raise ValueError("Metadata file must contain a list of tile records")
        records = [TileMetadata(**item) for item in payload]
        self.add_many(records)


def metadata_from_dict(data: Dict[str, Any]) -> TileMetadata:
    """Construct a validated metadata record from a JSON-compatible mapping."""

    return TileMetadata(
        tile_id=str(data["tile_id"]),
        scene_id=str(data["scene_id"]),
        sensor=str(data["sensor"]),
        date=str(data["date"]),
        bbox=[float(value) for value in data["bbox"]],
        resolution=float(data["resolution"]),
        cloud_cover=(None if data.get("cloud_cover") is None else float(data["cloud_cover"])),
        path=str(data["path"]),
        embedding_id=int(data["embedding_id"]),
        thumbnail=(None if data.get("thumbnail") is None else str(data["thumbnail"])),
    )


def group_overlapping_areas(records: Iterable[TileMetadata]) -> List[List[TileMetadata]]:
    """Group tiles into connected geographic areas using bbox intersection."""

    remaining = list(records)
    groups: List[List[TileMetadata]] = []
    while remaining:
        group = [remaining.pop(0)]
        changed = True
        while changed:
            changed = False
            for record in remaining[:]:
                if any(_bbox_overlaps(record.bbox, member.bbox) for member in group):
                    group.append(record)
                    remaining.remove(record)
                    changed = True
        groups.append(group)
    return groups


def _bbox_overlaps(first: List[float], second: List[float]) -> bool:
    return (
        max(first[0], second[0]) < min(first[2], second[2])
        and max(first[1], second[1]) < min(first[3], second[3])
    )