# 04 Merged-node audit (dot's round2_multisource_audit, 2026-10-30, read only)

## Purpose
LightRAG merges entities by name. Which nodes of experiment 01's original graph come from two or more patents? Is the sharing reasonable? Did merging create edges that no original text supports?

## Setup (differences from 01)
- No index built, no query run, **no API called** (additional cost $0). The input is experiment 01's **original** index (612 nodes / 994 edges), not the second run of 11-05.
- Source statistics: start from the union of each node's `source_id` and `entity_chunks`, group by publication number via `text_chunks.full_doc_id → full_docs`, and cross-check with the node's `file_path`.
- Semantic review: each of the 38 multi-source nodes was reviewed; every source was checked against the original text, the claim and the source chunk; every real adjacent edge of each node was checked against its own `source_id`. An AI-assisted review; 7 key nodes were reviewed a second time; not independent human annotation.

## Reproduce
```bash
experiments/04_merged_node_audit/run.sh offline
```
It runs `build_inventory.py` → `validate_reviews.py --require-complete` → `source_mapping_audit.py` → `check_original_documents.py` → `build_report.py`; compared with the committed originals only timestamps and path fields differ (measured on the author's machine, 2026-11-13). It reads experiment 01's original index, committed in [`../01_baseline_index_qa/index/`](../01_baseline_index_qa/index/README.md).

Figure (no API call):
```bash
pip install -r requirements-figures.txt
```
```bash
python tools/plot_merged_nodes.py
```

## Expected vs actual
| Item | Result | Source |
|---|---|---|
| multi-source nodes | 38 / 612 (6.21%): 28 from 2 patents, 6 from 3, 3 from 5, 1 from 9 | report 04, “statistics” and “source statistics” |
| classification | more specific shared technical concepts 3, reasonably shared broad classes 29, homonyms or document-local roles juxtaposed 6, insufficient evidence 0 | report 04, “statistics and decision boundaries” |
| ontology sensitivity | under a looser reading 3 / 34 / **1** (only Token remains) | same |
| mapping integrity | missing mappings, document conflicts and differences between KV and graph fields all 0; all 48 chunks can be located verbatim in the original texts | `source_mapping_audit.json` |
| adjacent edges | 307 per-node edge reviews (266 distinct edges); no unsupported edge caused by cross-patent merging confirmed; only 4 edges carry cross-patent sources themselves | report 04, “adjacent-edge check” |

Typical nodes (figure in the top-level README): **Token** juxtaposes “anonymisation substitute value” (US9118735B1) and “query token” (US9218390B2, US8655901B1) in one node; **Tokens** is reasonable sharing (both mean query tokens).

Report 04: [English translation](../../reports/translated/04_merged_node_audit_report_en.md) (the Chinese original prevails).

## Evidence
- `dossiers/N001–N038.json`: all sources, original quotes and real adjacent edges per node; `reviews/`: per-node reviews; `evidence/root_adjudications.json`: final decisions.
- `report/round2_multisource_nodes.{json,csv}`, `round2_multisource_sources.csv`: the 38 nodes and their 98 sources.
- `source_mapping_audit.json`: integrity check of the node/edge → chunk → document chain.

## Analysis and factors ruled out
- Sharing a broad class (Processor, Memory, Server and so on) is not an error in itself: instances in different patents are not interchangeable, but they can share a superclass.
- Juxtaposing homonyms is a **risk**: it makes path combinations without source constraints possible (for example Second User — Token — Label). But this audit ran no queries and did **not** show that the risk propagates into answers, so it is not reported as answer contamination that happened, nor classed as a code defect (P6, design trade-off).
- 3 within-source role warnings were also recorded (the acting subject in US9514120B1 extracted as Apparatus). Such problems first appear in single-patent raw extraction and are unrelated to cross-patent merging.

## Changes relative to dot's original
- [`PATH_CHANGES.diff`](PATH_CHANGES.diff): `ROOT` and the output directory now come from `paths.legacy_root()`, so offline replay does not write back into the committed originals. Paths only.
- `MANIFEST.json`, `SHA256SUMS.txt` and `package_validation.json` are dot's packaging metadata, kept unchanged. The paths in them are sanitised; for sanitised files the hash may differ from the original package.
- dot's scripts contain Chinese comments and a Chinese report template; they are kept as they were. `README_REPRODUCE.txt` is dot's original note.

## Original report
[`reports/original/04_merged_node_audit_report_zh.md`](../../reports/original/04_merged_node_audit_report_zh.md) (Chinese; [HTML](../../reports/original/04_merged_node_audit_report_zh.html)); [English translation](../../reports/translated/04_merged_node_audit_report_en.md).
