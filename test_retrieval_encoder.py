"""Focused tests for the backend-neutral RemoteCLIP adapter."""

import numpy as np
import pytest
import torch
from PIL import Image

from backend.retrieval.encoder import (
    RemoteCLIPConfig,
    RemoteCLIPEncoder,
    RemoteCLIPUnavailableError,
)


class FakeModel:
    def eval(self):
        return self

    def to(self, device):
        return self

    def encode_text(self, tokens):
        return torch.tensor([[3.0, 4.0]] * len(tokens))

    def encode_image(self, tensors):
        return torch.tensor([[0.0, 5.0]] * tensors.shape[0])


def test_remoteclip_encoder_normalizes_text_and_images():
    encoder = RemoteCLIPEncoder(
        RemoteCLIPConfig(batch_size=1),
        model=FakeModel(),
        tokenizer=lambda texts: torch.zeros((len(texts), 2)),
        image_preprocess=lambda image: torch.zeros((3, 2, 2)),
    )

    text_vectors = encoder.encode_text(["new construction", "water body"])
    image_vectors = encoder.encode_images(
        [Image.fromarray(np.zeros((2, 2, 3), dtype=np.uint8))]
    )

    np.testing.assert_allclose(text_vectors, [[0.6, 0.8], [0.6, 0.8]])
    np.testing.assert_allclose(image_vectors, [[0.0, 1.0]])
    assert encoder.dimension == 2


def test_remoteclip_requires_a_local_checkpoint_when_not_injected():
    encoder = RemoteCLIPEncoder(RemoteCLIPConfig(checkpoint_path=None))

    with pytest.raises(RemoteCLIPUnavailableError, match="checkpoint"):
        encoder.encode_text(["vegetation loss"])