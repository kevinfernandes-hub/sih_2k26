"""Hybrid semantic retrieval over the local tile index."""

from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

from .encoder import EmbeddingEncoder
from .metadata_store import MetadataStore
from .query_parser import QueryParser
from .ranking import RankingWeights, rank_result
from .vector_index import VectorIndex


class Retriever:
    """Connect query parsing, text encoding, FAISS search, and hybrid ranking."""

    def __init__(
        self,
        encoder: EmbeddingEncoder,
        index: VectorIndex,
        metadata: MetadataStore,
        *,
        parser: Optional[QueryParser] = None,
        weights: RankingWeights = RankingWeights(),
    ) -> None:
        self.encoder = encoder
        self.index = index
        self.metadata = metadata
        self.parser = parser or QueryParser()
        self.weights = weights

    def search(
        self,
        query: str,
        *,
        top_k: int = 15,
        reference_date: Optional[date] = None,
        point: Optional[tuple[float, float]] = None,
    ) -> Dict[str, Any]:
        parsed = self.parser.parse(query)
        query_vector = self.encoder.encode_text([parsed.semantic_query])
        # Retrieve more candidates initially to allow for deduplication
        scores, embedding_ids = self.index.search(query_vector, top_k=top_k * 3)
        
        from .metadata_store import _bbox_overlaps
        
        results = []
        seen_bboxes = []
        
        for semantic_score, embedding_id in zip(scores[0], embedding_ids[0]):
            if embedding_id < 0:
                continue
            record = self.metadata.get_by_embedding_id(int(embedding_id))
            
            # Deduplicate by spatial overlap
            is_duplicate = any(_bbox_overlaps(record.bbox, seen_bbox) for seen_bbox in seen_bboxes)
            if is_duplicate:
                continue
                
            seen_bboxes.append(record.bbox)
            results.append(
                rank_result(
                    record,
                    float(semantic_score),
                    parsed,
                    weights=self.weights,
                    reference_date=reference_date,
                    point=point,
                )
            )
            if len(results) >= top_k:
                break
                
        results.sort(key=lambda result: result["final_score"], reverse=True)
        return {"query": query, "parsed_query": parsed.to_dict(), "results": results}