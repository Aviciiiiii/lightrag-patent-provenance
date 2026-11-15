# Original LightRAG index of experiment 01

`patent_r2_full/` is the LightRAG working directory (workspace `patent_r2_full`) built by the **original run of experiment 01 on 2026-10-29** (dot's round2, `storage_full/`): 20 patents, 48 chunks, 612 nodes, 994 edges. The 12 files are copied byte for byte from dot's evidence package; their content is not changed. It is the input of the live reproduction (`tools/demo_context_provenance.py`), of experiment 04 (merged-node audit), and of the offline replay of experiment 01.

LightRAG v1.5.7 storage: GraphML graph, JSON key-value stores (including `kv_store_llm_response_cache.json`: 47 extraction, 26 query, 11 keyword and 2 summary entries) and NanoVectorDB vector stores (bge-m3, 1024 dimensions). Scripts never write here: the demo and offline replay work on copies in `runs/`.

## Checksums

[`SHA256SUMS.txt`](SHA256SUMS.txt) lists the SHA256 of all 12 files. Check with:

```bash
cd experiments/01_baseline_index_qa/index && shasum -a 256 -c SHA256SUMS.txt
```

## Evidence that this is the index of the original run

| Check | Result |
|---|---|
| hashes recorded by dot in the merged-node audit package, [`../../04_merged_node_audit/MANIFEST.json`](../../04_merged_node_audit/MANIFEST.json) (2026-10-30, path `round2/storage_full/patent_r2_full/`) | 9 files recorded, all 9 identical: `graph_chunk_entity_relation.graphml`, `kv_store_doc_status.json`, `kv_store_entity_chunks.json`, `kv_store_full_docs.json`, `kv_store_full_entities.json`, `kv_store_full_relations.json`, `kv_store_llm_response_cache.json`, `kv_store_relation_chunks.json`, `kv_store_text_chunks.json` |
| `input_hashes` in [`../../04_merged_node_audit/source_mapping_audit.json`](../../04_merged_node_audit/source_mapping_audit.json) | 8 files recorded, all identical |
| `index_hashes_before` / `index_hashes_after` in [`../evidence/retrieval_rank_probe.json`](../evidence/retrieval_rank_probe.json) (2026-10-29 14:47 UTC) and in `budget_sensitivity_index_integrity.json`, `supplement_budget_audit.json` | 3 files recorded (`vdb_chunks.json`, `kv_store_text_chunks.json`, `graph_chunk_entity_relation.graphml`), all identical |
| `vdb_entities.json`, `vdb_relationships.json` | no hash recorded in dot's material; byte-identical to `round2/storage_full/patent_r2_full/` in both copies of dot's evidence package that hold the original round2 results (`LightRAG_NEW_B`, `LightRAG_NEW_C`); every record in them was written on 2026-10-29 between 14:28 and 14:39 UTC (`__created_at__`) |

So 10 of the 12 files match hashes recorded by dot, and all 12 match dot's original evidence package (checked 2026-11-15).

## Content and licence

The index contains the indexed text of the 20 Dis2Pat patents (title, abstract, claims) and data derived from it (chunks, extracted entities and relations, their descriptions, embeddings, cached LLM extraction and query responses). It is shared under **CC-BY-SA-4.0**, like `data/`; see [`../../../data/LICENSE.md`](../../../data/LICENSE.md). Before it was added, all files were scanned for API keys (pattern and the actual key values of the run) and local absolute paths: no match.
