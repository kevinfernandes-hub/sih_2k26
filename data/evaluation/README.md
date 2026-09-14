# Evaluation Labels

`retrieval_queries.json` is intentionally empty until a human reviews the
current local tiles and assigns relevant tile IDs to each query. Empty labels
produce no Recall metrics; the benchmark reports `null` instead of fabricated
values.

`benchmark_queries.json` contains unlabeled queries used only for latency
measurement. It must not be used to claim Recall.

Once reviewed, use this structure:

```json
[
  {
    "query": "new construction",
    "relevant_tile_ids": ["reviewed_tile_id"]
  }
]
```