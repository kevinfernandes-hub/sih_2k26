# Local Retrieval Data

This directory is intentionally kept free of large imagery, model weights, and
generated indexes. Those files are ignored by Git.

## RemoteCLIP checkpoint

The encoder expects an official OpenCLIP-compatible RemoteCLIP state dict from
`chendelong/RemoteCLIP`. Supported architecture/checkpoint pairs are:

- `RN50` / `RemoteCLIP-RN50.pt`
- `ViT-B-32` / `RemoteCLIP-ViT-B-32.pt`
- `ViT-L-14` / `RemoteCLIP-ViT-L-14.pt`

The default local location is:

```text
data/models/remoteclip/RemoteCLIP-ViT-B-32.pt
```

Runtime does not download weights. Set an explicit path when needed:

```bash
export REMOTECLIP_MODEL_PATH="$PWD/data/models/remoteclip/RemoteCLIP-ViT-B-32.pt"
```

Download once during preparation, with network enabled:

```bash
.venv/bin/python -c 'from huggingface_hub import hf_hub_download; hf_hub_download("chendelong/RemoteCLIP", "RemoteCLIP-ViT-B-32.pt", local_dir="data/models/remoteclip")'
```

## Staged scene input

Put source `JPG`, `PNG`, or `TIFF` images under `data/staged/` or another input
directory. Each image must have a same-stem JSON sidecar:

```json
{
  "scene_id": "S2A_44QMD_20250101",
  "date": "2025-01-01",
  "sensor": "Sentinel-2",
  "bbox": [79.0, 21.0, 79.1, 21.1],
  "cloud_cover": 0.2
}
```

The sidecar is the source of scene identity, date, sensor, and geographic
extent. No metadata is invented by the ingestion command.

## Build the local index

```bash
.venv/bin/python -m backend.ingestion.prepare_demo \
  --input data/staged \
  --output data \
  --tile-size 512 \
  --overlap 0.10
```

Existing scene IDs in `data/manifests/scenes.json` are skipped. Generated tiles,
metadata, FAISS indexes, manifests, and model files stay local and are not
committed.

## Offline check

After model and index preparation, set `OFFLINE_MODE=true`, disable network
access, start the API, and query `/api/retrieval/index/status` followed by
`/api/retrieval/search`. A complete offline result requires all three local
assets: the checkpoint, FAISS index, and metadata JSON.