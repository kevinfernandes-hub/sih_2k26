"""Command-line preparation of a local staged satellite tile dataset."""

import argparse
import os
from pathlib import Path

from backend.retrieval.encoder import RemoteCLIPConfig, RemoteCLIPEncoder

from .incremental_ingest import IncrementalIngester


def main() -> None:
    parser = argparse.ArgumentParser(description="Index staged local satellite scenes for offline retrieval")
    parser.add_argument("--input", "--input-dir", dest="input_dir", type=Path, required=True, help="Directory containing images and JSON sidecars")
    parser.add_argument("--output", "--data-dir", dest="data_dir", type=Path, default=Path("data"))
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--tile-size", type=int, default=512)
    parser.add_argument("--overlap", type=float, default=0.0)
    args = parser.parse_args()

    model_path = args.model_path or Path(
        os.environ.get("REMOTECLIP_MODEL_PATH", args.data_dir / "models" / "remoteclip" / "RemoteCLIP-ViT-B-32.pt")
    )
    encoder = RemoteCLIPEncoder(RemoteCLIPConfig(checkpoint_path=model_path))
    result = IncrementalIngester(
        args.data_dir,
        encoder,
        tile_size=args.tile_size,
        overlap=args.overlap,
    ).ingest(args.input_dir)
    print(
        f"Indexed {result.tiles_added} new tiles from {result.scenes_added} scenes "
        f"({result.scenes_seen} scenes scanned)."
    )


if __name__ == "__main__":
    main()