"""Backend-neutral interfaces for satellite imagery retrieval."""

from .encoder import (
    EmbeddingEncoder,
    EncoderError,
    RemoteCLIPArchitectureError,
    RemoteCLIPCheckpointError,
    RemoteCLIPConfig,
    RemoteCLIPEncoder,
    RemoteCLIPUnavailableError,
)
from .metadata_store import MetadataStore, TileMetadata, group_overlapping_areas, metadata_from_dict
from .vector_index import VectorIndex, VectorIndexError
from .query_parser import QueryParser, RetrievalQuery, parse_query
from .ranking import RankingWeights, rank_result
from .retriever import Retriever
from .analysis_service import RetrievalAnalysisService
from .pipeline_adapter import PipelineInput, pipeline_input_from_pair, run_existing_pipeline
from .evidence_fusion import EvidenceWeights, fuse_change_evidence

__all__ = [
    "EmbeddingEncoder",
    "EncoderError",
    "RemoteCLIPArchitectureError",
    "RemoteCLIPCheckpointError",
    "RemoteCLIPConfig",
    "RemoteCLIPEncoder",
    "RemoteCLIPUnavailableError",
    "MetadataStore",
    "TileMetadata",
    "metadata_from_dict",
    "group_overlapping_areas",
    "VectorIndex",
    "VectorIndexError",
    "QueryParser",
    "RetrievalQuery",
    "parse_query",
    "RankingWeights",
    "rank_result",
    "Retriever",
    "RetrievalAnalysisService",
    "PipelineInput",
    "pipeline_input_from_pair",
    "run_existing_pipeline",
    "EvidenceWeights",
    "fuse_change_evidence",
]