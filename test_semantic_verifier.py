import json
from pathlib import Path

import numpy as np

from backend.retrieval.semantic_verifier import compute_cosine_similarity, verify_image_semantics


class MockEncoderConfig:
    model_name = "MockRemoteCLIP-ViT-B-32"


class MockRemoteCLIPEncoder:
    def __init__(self, config=None):
        self.config = config or MockEncoderConfig()

    def encode_text(self, texts):
        # Return a mock normalized vector of size 512
        vec = np.ones(512)
        vec[0] = 0.5  # add some variation
        return [vec / np.linalg.norm(vec)] * len(texts)

    def encode_images(self, images):
        # Return a mock normalized vector of size 512
        vec = np.ones(512)
        vec[1] = 0.2  # slightly different variation
        return [vec / np.linalg.norm(vec)] * len(images)


def test_compute_cosine_similarity():
    vec_a = np.array([1.0, 0.0, 0.0])
    vec_b = np.array([1.0, 0.0, 0.0])
    assert np.isclose(compute_cosine_similarity(vec_a, vec_b), 1.0)

    vec_c = np.array([0.0, 1.0, 0.0])
    assert np.isclose(compute_cosine_similarity(vec_a, vec_c), 0.0)

    vec_d = np.array([0.0, 0.0, 0.0])
    assert compute_cosine_similarity(vec_a, vec_d) == 0.0


def test_verify_image_semantics_success(tmp_path: Path):
    encoder = MockRemoteCLIPEncoder()
    image_path = tmp_path / "test_image.png"
    image_path.touch()

    # Call with cache_dir
    cache_dir = tmp_path / "cache"
    result = verify_image_semantics(
        query="vegetation loss",
        image_path=image_path,
        encoder=encoder,
        cache_dir=cache_dir,
        location_id="test_loc"
    )

    assert result.get("verified") is True
    assert result["query"] == "vegetation loss"
    assert "semantic_similarity" in result
    assert result["model"] == "RemoteCLIP"
    assert result["checkpoint"] == "MockRemoteCLIP-ViT-B-32"

    # Verify that caching works
    assert cache_dir.exists()
    cache_files = list(cache_dir.glob("*.json"))
    assert len(cache_files) == 1

    # Re-run and hit cache
    cached_result = verify_image_semantics(
        query="vegetation loss",
        image_path=image_path,
        encoder=encoder,
        cache_dir=cache_dir,
        location_id="test_loc"
    )
    assert cached_result["semantic_similarity"] == result["semantic_similarity"]


def test_verify_image_semantics_invalid_image(tmp_path: Path):
    # Pass an encoder that raises an error for images
    class FailingEncoder:
        def encode_text(self, texts):
            return [np.zeros(512)]
        def encode_images(self, images):
            raise ValueError("Invalid image")

    encoder = FailingEncoder()
    result = verify_image_semantics(
        query="vegetation loss",
        image_path=tmp_path / "missing.png",
        encoder=encoder
    )

    assert result["verified"] is False
    assert result["semantic_similarity"] == 0.0
    assert "error" in result
