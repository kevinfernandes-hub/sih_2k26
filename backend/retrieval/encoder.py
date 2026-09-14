"""Remote-sensing image and text embedding adapters.

The retrieval system depends on this small interface rather than on a model
implementation. RemoteCLIP is loaded lazily so the existing API can continue
to run when the optional model runtime or checkpoint is not installed.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Protocol, Sequence, Union

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np
from PIL import Image


ImageInput = Union[Image.Image, str, Path]


class EncoderError(RuntimeError):
    """Base error raised by retrieval encoders."""


class RemoteCLIPUnavailableError(EncoderError):
    """Raised when the optional RemoteCLIP runtime or checkpoint is unavailable."""


class RemoteCLIPCheckpointError(EncoderError):
    """Raised when a local checkpoint is not an OpenCLIP-compatible state dict."""


class RemoteCLIPArchitectureError(EncoderError):
    """Raised when checkpoint weights do not match the configured architecture."""


class EmbeddingEncoder(Protocol):
    """Interface implemented by text/image embedding models."""

    def encode_text(self, texts: Sequence[str]) -> np.ndarray:
        """Return one embedding row per text query."""

    def encode_images(self, images: Sequence[ImageInput]) -> np.ndarray:
        """Return one embedding row per image."""


@dataclass(frozen=True)
class RemoteCLIPConfig:
    """Runtime settings for a local RemoteCLIP checkpoint."""

    model_name: str = "ViT-B-32"
    checkpoint_path: Optional[Path] = None
    device: Optional[str] = None
    batch_size: int = 16

    @classmethod
    def from_environment(cls) -> "RemoteCLIPConfig":
        """Build configuration from the explicit local model-path setting."""

        model_path = os.environ.get("REMOTECLIP_MODEL_PATH", "").strip()
        return cls(checkpoint_path=Path(model_path).expanduser() if model_path else None)


class RemoteCLIPEncoder:
    """Encode text and satellite imagery with a local RemoteCLIP checkpoint.

    ``open_clip_torch`` and the RemoteCLIP checkpoint are intentionally
    optional at import time. Pass a model, tokenizer, and image preprocessor
    in tests or custom deployments to avoid loading the model twice.
    """

    def __init__(
        self,
        config: Optional[RemoteCLIPConfig] = None,
        *,
        model: Optional[Any] = None,
        tokenizer: Optional[Any] = None,
        image_preprocess: Optional[Any] = None,
    ) -> None:
        self.config = config or RemoteCLIPConfig.from_environment()
        if self.config.batch_size < 1:
            raise ValueError("RemoteCLIP batch_size must be greater than zero")

        self._model = model
        self._tokenizer = tokenizer
        self._image_preprocess = image_preprocess
        self._torch = None
        self._device = None
        self._dimension: Optional[int] = None

        if self._model is not None:
            self._load_torch_runtime()

    @property
    def dimension(self) -> Optional[int]:
        """Embedding dimension after the first successful encode operation."""

        return self._dimension

    def encode_text(self, texts: Sequence[str]) -> np.ndarray:
        """Encode text queries and return L2-normalized float32 vectors."""

        text_list = list(texts)
        if not text_list:
            return np.empty((0, 0), dtype=np.float32)
        self._ensure_loaded()
        assert self._model is not None
        assert self._tokenizer is not None
        assert self._torch is not None

        batches: List[np.ndarray] = []
        with self._torch.no_grad():
            for start in range(0, len(text_list), self.config.batch_size):
                tokens = self._tokenizer(text_list[start : start + self.config.batch_size])
                tokens = tokens.to(self._device)
                vectors = self._model.encode_text(tokens)
                batches.append(self._normalise(vectors))
        return self._stack_batches(batches)

    def encode_images(self, images: Sequence[ImageInput]) -> np.ndarray:
        """Encode images and return L2-normalized float32 vectors."""

        image_list = list(images)
        if not image_list:
            return np.empty((0, 0), dtype=np.float32)
        self._ensure_loaded()
        assert self._model is not None
        assert self._image_preprocess is not None
        assert self._torch is not None

        batches: List[np.ndarray] = []
        with self._torch.no_grad():
            for start in range(0, len(image_list), self.config.batch_size):
                batch = image_list[start : start + self.config.batch_size]
                tensors = self._torch.stack(
                    [self._image_preprocess(self._open_image(image)) for image in batch]
                ).to(self._device)
                vectors = self._model.encode_image(tensors)
                batches.append(self._normalise(vectors))
        return self._stack_batches(batches)

    def _ensure_loaded(self) -> None:
        if self._model is not None and self._tokenizer is not None and self._image_preprocess is not None:
            return
        self._load_remoteclip()

    def _load_torch_runtime(self) -> None:
        try:
            import torch
        except ImportError as exc:
            raise RemoteCLIPUnavailableError(
                "RemoteCLIP requires PyTorch. Install the project requirements first."
            ) from exc
        self._torch = torch
        torch.set_num_threads(1)
        device_name = self.config.device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._device = torch.device(device_name)
        self._model.to(self._device)
        self._model.eval()

    def _load_remoteclip(self) -> None:
        if self.config.checkpoint_path is None:
            raise RemoteCLIPUnavailableError(
                "No RemoteCLIP checkpoint configured. Pass "
                "RemoteCLIPConfig(checkpoint_path=...)."
            )
        checkpoint = self.config.checkpoint_path.expanduser().resolve()
        if not checkpoint.is_file():
            raise RemoteCLIPUnavailableError(
                "RemoteCLIP checkpoint was not found: " + str(checkpoint)
            )
        try:
            import torch
            import open_clip
        except ImportError as exc:
            raise RemoteCLIPUnavailableError(
                "RemoteCLIP requires torch and open_clip_torch; install requirements.txt."
            ) from exc

        try:
            if self.config.model_name not in {"RN50", "ViT-B-32", "ViT-L-14"}:
                raise RemoteCLIPArchitectureError(
                    "Unsupported RemoteCLIP architecture: " + self.config.model_name
                )
            model, _, preprocess = open_clip.create_model_and_transforms(
                self.config.model_name,
                pretrained=None,
                pretrained_text=False,
            )
            tokenizer = open_clip.get_tokenizer(self.config.model_name)
            checkpoint_data = torch.load(str(checkpoint), map_location="cpu", weights_only=True)
            state_dict = checkpoint_data.get("state_dict", checkpoint_data) if isinstance(checkpoint_data, dict) else None
            if not isinstance(state_dict, dict) or not state_dict:
                raise RemoteCLIPCheckpointError(
                    "RemoteCLIP checkpoint must contain an OpenCLIP state dictionary: " + str(checkpoint)
                )
            state_dict = {
                key.removeprefix("module."): value for key, value in state_dict.items()
            }
            model.load_state_dict(state_dict, strict=True)
        except RemoteCLIPArchitectureError:
            raise
        except RemoteCLIPCheckpointError:
            raise
        except RuntimeError as exc:
            raise RemoteCLIPArchitectureError(
                "RemoteCLIP checkpoint is incompatible with architecture "
                + self.config.model_name
                + ": "
                + str(exc)
            ) from exc
        except Exception as exc:
            raise RemoteCLIPUnavailableError(
                "Unable to load the local RemoteCLIP checkpoint from " + str(checkpoint) + ": " + str(exc)
            ) from exc

        self._model = model
        self._tokenizer = tokenizer
        self._image_preprocess = preprocess
        self._load_torch_runtime()

    @staticmethod
    def _open_image(image: ImageInput) -> Image.Image:
        if isinstance(image, Image.Image):
            return image.convert("RGB")
        return Image.open(image).convert("RGB")

    def _normalise(self, vectors: Any) -> np.ndarray:
        assert self._torch is not None
        normalised = self._torch.nn.functional.normalize(vectors.float(), dim=-1)
        result = normalised.detach().cpu().numpy().astype(np.float32, copy=False)
        if result.ndim != 2:
            raise EncoderError("RemoteCLIP returned embeddings with an invalid shape")
        if self._dimension is None:
            self._dimension = int(result.shape[1])
        elif result.shape[1] != self._dimension:
            raise EncoderError("RemoteCLIP returned inconsistent embedding dimensions")
        return result

    @staticmethod
    def _stack_batches(batches: Sequence[np.ndarray]) -> np.ndarray:
        return np.concatenate(batches, axis=0).astype(np.float32, copy=False)