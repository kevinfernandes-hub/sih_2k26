# Dataset and Offline Retrieval

## Current demo versus scalable architecture

The architecture supports many areas, sensors, dates, and tiles. The current
checked local demo is intentionally small and contains only existing repository
Nandanvan imagery:

- 2 scenes: 2022-02-22 and 2025-02-26
- 4 tiles
- 1 geographic area
- 1 temporal pair
- Sentinel-2 imagery at 10 m metadata resolution

No additional areas or dates are claimed until real source imagery and reviewed
sidecars are supplied.

## Directory structure

```text
data/
  raw/<area>/           optional source imagery archive
  staged/               source images plus same-stem JSON sidecars
  tiles/                generated local tiles
  metadata/tiles.json   tile metadata and embedding IDs
  indexes/              persistent FAISS indexes
  models/remoteclip/    local RemoteCLIP checkpoint, ignored by Git
  manifests/scenes.json indexed scenes and per-scene tile IDs
  evaluation/           manually reviewed retrieval labels
```

## Scene sidecar

Every staged image needs a JSON sidecar:

```json
{
  "scene_id": "S2_NAGPUR_20250226",
  "sensor": "Sentinel-2",
  "date": "2025-02-26",
  "bbox": [79.0, 21.0, 79.1, 21.1],
  "resolution": 10,
  "cloud_cover": 0.2
}
```

The source sidecar is authoritative. Ingestion does not invent scene labels.
JPG, PNG, and TIFF inputs are supported.

## Model and embeddings

The local encoder uses the official OpenCLIP-compatible RemoteCLIP
`ViT-B-32` checkpoint. The current embedding dimension is 512. Runtime reads
`REMOTECLIP_MODEL_PATH` and never downloads weights.

## Ingestion

```bash
.venv/bin/python -m backend.ingestion.prepare_demo \
  --input data/staged \
  --output data \
  --tile-size 512 \
  --overlap 0.10
```

Scene IDs already in `data/manifests/scenes.json` are skipped. New scenes only
generate tiles, embeddings, metadata, and FAISS entries for those scenes.

## Evaluation

Run measured index statistics:

```bash
.venv/bin/python -m backend.evaluation.benchmark
```

Add manually reviewed retrieval labels before requesting Recall@K:

```bash
.venv/bin/python -m backend.evaluation.benchmark \
  --labels data/evaluation/retrieval_queries.json
```

Change Precision, Recall, F1, and IoU are available when reviewed predicted
and ground-truth masks are supplied to `binary_metrics`.

## Offline operation

Set `OFFLINE_MODE=true`, provide the local model path, and ensure local FAISS,
metadata, and tile files exist. Semantic retrieval requires no external
satellite API. The existing change pipeline may still use its configured online
data sources when explicitly invoked; retrieval itself remains local.