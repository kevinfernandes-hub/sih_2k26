"""Discover staged satellite scenes and their sidecar metadata."""

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable, List, Optional


@dataclass(frozen=True)
class SceneRecord:
    scene_id: str
    sensor: str
    date: str
    path: Path
    bbox: List[float]
    cloud_cover: Optional[float] = None


def scan_scenes(input_dir: Path) -> List[SceneRecord]:
    """Scan images with ``.json`` sidecars for incremental ingestion."""

    records: List[SceneRecord] = []
    for image_path in sorted(Path(input_dir).rglob("*")):
        if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}:
            continue
        sidecar_path = image_path.with_suffix(".json")
        sidecar = _read_sidecar(sidecar_path)
        scene_id = str(sidecar.get("scene_id") or image_path.stem)
        scene_date = str(sidecar.get("date") or _date_from_name(image_path.stem))
        bbox = sidecar.get("bbox")
        if bbox is None:
            raise ValueError("Scene sidecar must define bbox: " + str(sidecar_path))
        records.append(
            SceneRecord(
                scene_id=scene_id,
                sensor=str(sidecar.get("sensor", "Sentinel-2")),
                date=scene_date,
                path=image_path,
                bbox=[float(value) for value in bbox],
                cloud_cover=(None if sidecar.get("cloud_cover") is None else float(sidecar["cloud_cover"])),
            )
        )
    return records


def _read_sidecar(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Scene sidecar must contain a JSON object: " + str(path))
    return payload


def _date_from_name(name: str) -> str:
    match = re.search(r"(?<!\d)(20\d{6})(?!\d)", name)
    if not match:
        raise ValueError("Scene date missing from filename or sidecar: " + name)
    value = match.group(1)
    return date.fromisoformat(value[:4] + "-" + value[4:6] + "-" + value[6:]) .isoformat()