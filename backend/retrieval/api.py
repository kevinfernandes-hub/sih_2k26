"""FastAPI routes for offline semantic satellite retrieval."""

import os
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .analysis_service import RetrievalAnalysisService
from .encoder import EncoderError, RemoteCLIPConfig, RemoteCLIPEncoder, RemoteCLIPUnavailableError
from .evidence_fusion import fuse_change_evidence
from .metadata_store import MetadataStore, group_overlapping_areas
from .retriever import Retriever
from .vector_index import VectorIndex, VectorIndexError
from backend.ingestion.incremental_ingest import IncrementalIngester


router = APIRouter(prefix="/api/retrieval", tags=["retrieval"])
_SERVICE: Optional[RetrievalAnalysisService] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(10, ge=1, le=100)
    reference_date: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class AnalyzeRequest(BaseModel):
    tile_id: str = Field(..., min_length=1)
    mode: str = Field("latest", pattern="^(latest|previous|custom)$")
    before_date: Optional[str] = None
    after_date: Optional[str] = None
    execute_change_pipeline: bool = False
    location_name: Optional[str] = None


class IngestRequest(BaseModel):
    input_dir: Optional[str] = None
    tile_size: int = Field(512, ge=16, le=4096)
    overlap: float = Field(0.0, ge=0.0, lt=1.0)


def _paths() -> Dict[str, Path]:
    root = Path(__file__).resolve().parents[2]
    data_dir = Path(os.environ.get("RETRIEVAL_DATA_DIR", root / "data"))
    return {
        "metadata": Path(os.environ.get("RETRIEVAL_METADATA_PATH", data_dir / "metadata" / "tiles.json")),
        "index": Path(os.environ.get("RETRIEVAL_INDEX_PATH", data_dir / "indexes" / "satellite.index")),
        "model": Path(
            os.environ.get(
            "REMOTECLIP_MODEL_PATH",
                os.environ.get(
                    "RETRIEVAL_MODEL_PATH",
                    data_dir / "models" / "remoteclip" / "RemoteCLIP-ViT-B-32.pt",
                ),
            )
        ),
    }


def _service() -> RetrievalAnalysisService:
    global _SERVICE
    if _SERVICE is None:
        paths = _paths()
        if not paths["model"].is_file():
            raise RemoteCLIPUnavailableError(
                "RemoteCLIP checkpoint was not found: " + str(paths["model"])
            )
        metadata = MetadataStore(paths["metadata"])
        index = VectorIndex(paths["index"])
        if paths["index"].is_file():
            index.load()
        encoder = RemoteCLIPEncoder(RemoteCLIPConfig(checkpoint_path=paths["model"]))
        _SERVICE = RetrievalAnalysisService(
            retriever=Retriever(encoder, index, metadata),
            metadata=metadata,
        )
    return _SERVICE


def _parse_reference_date(value: Optional[str]) -> Optional[date]:
    return None if value is None else date.fromisoformat(value)


@router.post("/search")
def search_retrieval(request: SearchRequest) -> Dict[str, Any]:
    try:
        return _service().search(
            request.query,
            top_k=request.top_k,
            reference_date=_parse_reference_date(request.reference_date),
            point=(request.longitude, request.latitude)
            if request.longitude is not None and request.latitude is not None
            else None,
        )
    except (EncoderError, VectorIndexError, FileNotFoundError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/analyze")
def prepare_retrieval_analysis(request: AnalyzeRequest) -> Dict[str, Any]:
    try:
        if request.execute_change_pipeline:
            plan = _service().analyze(
                request.tile_id,
                mode=request.mode,
                before_date=request.before_date,
                after_date=request.after_date,
                location_name=request.location_name,
            )
            change = plan["change"]
            pipeline_invoked = True
        else:
            plan = _service().prepare_analysis(
                request.tile_id,
                mode=request.mode,
                before_date=request.before_date,
                after_date=request.after_date,
            )
            change = {"status": "prepared", "pipeline_invoked": False}
            pipeline_invoked = False
        return {
            "retrieval": {"tile_id": request.tile_id},
            "temporal": plan["timeline"],
            "change": change,
            "pipeline_invoked": pipeline_invoked,
            "analysis": plan["change_analysis"],
            "evidence": fuse_change_evidence(
                retrieval={"parsed_query": {}, "semantic_score": 0.0},
                temporal=plan["timeline"],
                change=change if pipeline_invoked else None,
            ),
        }
    except (EncoderError, VectorIndexError, FileNotFoundError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/index/status")
def retrieval_index_status() -> Dict[str, Any]:
    paths = _paths()
    metadata = MetadataStore(paths["metadata"])
    records = metadata.all()
    dates = [record.date for record in records]
    indexed_area_bbox = None
    embedding_dimension = None
    if paths["index"].exists():
        try:
            local_index = VectorIndex(paths["index"])
            local_index.load()
            embedding_dimension = local_index.dimension
        except VectorIndexError:
            pass
    if records:
        indexed_area_bbox = [
            min(record.bbox[0] for record in records),
            min(record.bbox[1] for record in records),
            max(record.bbox[2] for record in records),
            max(record.bbox[3] for record in records),
        ]
    areas = group_overlapping_areas(records)
    temporal_pairs = sum(
        max(0, len({record.date for record in area}) - 1)
        for area in areas
    )
    return {
        "indexed_tiles": len(records),
        "metadata_count": len(records),
        "indexed_scenes": len({record.scene_id for record in records}),
        "geographic_areas": len(areas),
        "temporal_pairs": temporal_pairs,
        "embedding_dimension": embedding_dimension,
        "sensors": sorted({record.sensor for record in records}),
        "date_range": {"start": min(dates) if dates else None, "end": max(dates) if dates else None},
        "indexed_area_bbox": indexed_area_bbox,
        "index_size_bytes": paths["index"].stat().st_size if paths["index"].exists() else 0,
        "last_update": _last_update(paths),
        "metadata_path": str(paths["metadata"]),
        "index_path": str(paths["index"]),
        "model_configured": paths["model"].is_file(),
        "offline_ready": paths["metadata"].is_file() and paths["index"].is_file() and paths["model"].is_file(),
        "offline_mode": os.environ.get("OFFLINE_MODE", "true").lower() == "true",
    }


@router.post("/ingest")
def ingest_retrieval_data(request: IngestRequest) -> Dict[str, Any]:
    paths = _paths()
    root = Path(__file__).resolve().parents[2]
    data_dir = Path(os.environ.get("RETRIEVAL_DATA_DIR", root / "data"))
    input_dir = Path(request.input_dir) if request.input_dir else data_dir / "staged"
    if not input_dir.is_dir():
        raise HTTPException(status_code=400, detail="Input scene directory was not found: " + str(input_dir))
    try:
        encoder = RemoteCLIPEncoder(RemoteCLIPConfig(checkpoint_path=paths["model"]))
        result = IncrementalIngester(
            data_dir,
            encoder,
            tile_size=request.tile_size,
            overlap=request.overlap,
        ).ingest(input_dir)
        return {
            "status": "ok",
            "scenes_seen": result.scenes_seen,
            "scenes_added": result.scenes_added,
            "tiles_added": result.tiles_added,
            "offline_mode": os.environ.get("OFFLINE_MODE", "true").lower() == "true",
        }
    except (EncoderError, VectorIndexError, FileNotFoundError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _last_update(paths: Dict[str, Path]) -> Optional[str]:
    candidates = [path.stat().st_mtime for path in (paths["metadata"], paths["index"]) if path.exists()]
    if not candidates:
        return None
    return datetime.fromtimestamp(max(candidates)).isoformat(timespec="seconds")