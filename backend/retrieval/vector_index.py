"""Offline FAISS index for normalized satellite tile embeddings."""

from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np


class VectorIndexError(RuntimeError):
    """Raised when a vector index cannot be used safely."""


class VectorIndex:
    """Persistent cosine-similarity index backed by FAISS inner product search."""

    def __init__(self, path: Path, dimension: Optional[int] = None) -> None:
        self.path = Path(path)
        self.dimension = dimension
        self._index = None

    @property
    def size(self) -> int:
        return 0 if self._index is None else int(self._index.ntotal)

    def create(self, dimension: int) -> None:
        if dimension < 1:
            raise ValueError("Vector dimension must be greater than zero")
        faiss = self._faiss()
        self.dimension = dimension
        self._index = faiss.IndexIDMap2(faiss.IndexFlatIP(dimension))

    def load(self) -> None:
        if not self.path.exists():
            raise VectorIndexError("Vector index was not found: " + str(self.path))
        faiss = self._faiss()
        self._index = faiss.read_index(str(self.path))
        loaded_dimension = int(self._index.d)
        if self.dimension is not None and self.dimension != loaded_dimension:
            raise VectorIndexError("Vector index dimension does not match configuration")
        self.dimension = loaded_dimension

    def add(self, vectors: np.ndarray, embedding_ids: Sequence[int]) -> None:
        self._ensure_index(vectors)
        values = self._prepare_vectors(vectors)
        ids = np.asarray(list(embedding_ids), dtype=np.int64)
        if len(values) != len(ids):
            raise ValueError("Each vector must have one embedding ID")
        if len(ids) != len(set(ids.tolist())):
            raise ValueError("Embedding IDs must be unique within an insert")
        existing_ids = self._indexed_ids()
        if existing_ids.intersection(ids.tolist()):
            raise ValueError("Embedding ID already exists in vector index")
        self._index.add_with_ids(values, ids)

    def search(self, query: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        if self._index is None:
            raise VectorIndexError("Vector index has not been created or loaded")
        if top_k < 1:
            raise ValueError("top_k must be greater than zero")
        values = self._prepare_vectors(query)
        scores, ids = self._index.search(values, min(top_k, self.size))
        return scores, ids

    def save(self) -> None:
        if self._index is None:
            raise VectorIndexError("Cannot save an empty, uninitialized vector index")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(self.path.suffix + ".tmp")
        self._faiss().write_index(self._index, str(temporary_path))
        temporary_path.replace(self.path)

    def ids(self) -> List[int]:
        return sorted(self._indexed_ids())

    def _ensure_index(self, vectors: np.ndarray) -> None:
        values = np.asarray(vectors)
        if values.ndim != 2:
            raise ValueError("Vectors must be a two-dimensional array")
        if self._index is None:
            self.create(int(values.shape[1]))

    def _prepare_vectors(self, vectors: np.ndarray) -> np.ndarray:
        values = np.asarray(vectors, dtype=np.float32)
        if values.ndim != 2 or values.shape[1] != self.dimension:
            raise ValueError("Vectors do not match the index dimension")
        norms = np.linalg.norm(values, axis=1, keepdims=True)
        if np.any(norms == 0):
            raise ValueError("Zero-length vectors cannot be indexed or searched")
        return values / norms

    def _indexed_ids(self) -> set[int]:
        if self._index is None or self.size == 0:
            return set()
        return set(self._faiss().vector_to_array(self._index.id_map).tolist())

    @staticmethod
    def _faiss():
        try:
            import faiss
        except ImportError as exc:
            raise VectorIndexError(
                "FAISS is required for local vector search. Install faiss-cpu."
            ) from exc
        faiss.omp_set_num_threads(1)
        return faiss