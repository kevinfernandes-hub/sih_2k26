# Evaluation

Run measured local-index statistics:

```bash
.venv/bin/python -m backend.evaluation.benchmark
```

To calculate Recall@1/5/10, provide reviewed relevance labels. The file must
map each natural-language query to one or more relevant tile IDs:

```json
{
  "new construction": ["S2_NANDANVAN_20250226_000_000"],
  "water bodies": ["reviewed_tile_id"]
}
```

```bash
.venv/bin/python -m backend.evaluation.benchmark \
  --labels data/manifests/retrieval_labels.json \
  --output data/manifests/benchmark.json
```

Change Precision, Recall, F1, and IoU are available through
`backend.evaluation.change_metrics.binary_metrics` when reviewed prediction
and ground-truth masks are supplied. No quality metric is produced without
those labels.
