import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

from backend.retrieval.encoder import EmbeddingEncoder

LOGGER = logging.getLogger(__name__)


def compute_cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    # Normalize before dot product to ensure stability and strictly match cosine logic
    vec_a_norm = vec_a / norm_a
    vec_b_norm = vec_b / norm_b
    
    return float(np.dot(vec_a_norm, vec_b_norm))


def verify_image_semantics(
    query: str,
    image_path: Path,
    encoder: EmbeddingEncoder,
    cache_dir: Optional[Path] = None,
    location_id: str = "unknown",
) -> Dict[str, Any]:
    """
    Verify the semantic relevance of an acquired satellite image against a text query.
    """
    model_version = getattr(encoder.config, "model_name", "RemoteCLIP-Unknown") if hasattr(encoder, "config") else "Unknown"
    
    # Try cache
    cache_file = None
    if cache_dir:
        # Create a unique key for the image based on its path (or hash). 
        # Since image_path is unique for a location/date, its name suffices.
        safe_query = "".join(c if c.isalnum() else "_" for c in query.lower())
        cache_key = f"{location_id}_{image_path.stem}_{safe_query}_{model_version}.json"
        cache_file = cache_dir / cache_key
        
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    cached_data = json.load(f)
                    LOGGER.info(f"[SEMANTIC VERIFY] Cache hit for {query} on {image_path.name}")
                    return cached_data
            except Exception as e:
                LOGGER.warning(f"Failed to read semantic verification cache: {e}")

    # Not in cache, compute
    try:
        LOGGER.info(f"[SEMANTIC VERIFY] Encoding query: '{query}'")
        query_emb = encoder.encode_text([query])[0]
        
        LOGGER.info(f"[SEMANTIC VERIFY] Encoding image: {image_path}")
        image_emb = encoder.encode_images([image_path])[0]
        
        similarity = compute_cosine_similarity(query_emb, image_emb)
        
        result = {
            "query": query,
            "image_path": str(image_path),
            "semantic_similarity": similarity,
            "model": "RemoteCLIP",
            "checkpoint": model_version,
            "verified": True
        }
        
        if cache_dir and cache_file:
            cache_dir.mkdir(parents=True, exist_ok=True)
            try:
                with open(cache_file, "w") as f:
                    json.dump(result, f)
            except Exception as e:
                LOGGER.warning(f"Failed to write semantic verification cache: {e}")
                
        return result
    except Exception as e:
        LOGGER.error(f"[SEMANTIC VERIFY] Error verifying image {image_path}: {e}")
        return {
            "query": query,
            "image_path": str(image_path),
            "semantic_similarity": 0.0,
            "model": "RemoteCLIP",
            "checkpoint": model_version,
            "verified": False,
            "error": str(e)
        }
