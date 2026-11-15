# 03 Chunk boundary, full pipeline (dot's round4_full_20261030, 2026-10-30)

> Naming: the folder is called round4, but the report calls itself the “third-round Chunk Boundary Ablation complete-pipeline supplementary report”. This repository calls it **03** ([mapping](../../docs/NAMING.md)).

## Purpose
Test 02's artificial-chunking result in the complete pipeline: with full patent documents, change only the chunk boundary and see whether it affects the extracted relations, the merged graph, natural retrieval and the final answer; and find the earliest stage at which an error appears.

## Setup (differences from 01)
- 3 groups of full patents (title + abstract + all claims): **F01** US9589231B2, **F05** US8069128B2, **F04** US8509827B2. 2 conditions × 3 repeats per group, **18 independent indexes**, each containing a single patent.
- Conditions (dot's names A/B, [mapping](../../docs/NAMING.md#2-condition-names-inside-the-experiments)):
  - **same-chunk boundary**: the target evidence falls into one chunk;
  - **cross-chunk boundary**: no chunk contains both kinds of target evidence.
  Both use chunks of at most 1200 tokens, an exact 100-token overlap between neighbours, and unchanged content and order; the pre-frozen token windows are passed through LightRAG's official `chunking_func` extension point ([`scripts/custom_chunker.py`](scripts/custom_chunker.py)).
- Frozen questions and criteria: [`conditions/frozen_groups.json`](conditions/frozen_groups.json). Each run does: extraction → official parsing → merged graph → natural `mix` QA → forced diagnostic with the original text given directly (not counted as a natural result); a `naive` QA is appended at the end.
- Every run uses a fresh working directory; no extraction, answer or embedding cache is reused. Interleaved order A1/B1/B2/A2/A3/B3.
- 117 LLM and 247 embedding calls in total; 2 extractions were truncated (both in F01's same-chunk condition), so clean pairs are compared separately.

## Reproduce
```bash
experiments/03_chunk_boundary_full_pipeline/run.sh check
```
`check` re-chunks the 6 conditions with dot's chunker and compares the 15 saved chunks by SHA256 (no API call).
```bash
experiments/03_chunk_boundary_full_pipeline/run.sh offline
```
Paid rerun: `run.sh live new`, then `LRP_CONFIRM_COSTS=yes run.sh live F01`, `F05`, `F04`, `naive` in this order. `naive` must run after all 18 indexes are complete. The original run took about 19 minutes and is estimated at CNY 1.08–1.33 (not an invoice); in-script hard cap CNY 4.

## Expected vs actual
| Group | Condition | target predicates all in the merged graph's relation records | mix retrieves all target text | mix core answer correct | forced diagnostic correct | runs without truncation |
|---|---|---|---|---|---|---|
| F01 | same chunk | 3/3 | 3/3 | 3/3 | 3/3 | 1 |
| F01 | cross chunk | **0/3** | 3/3 | 3/3 | 3/3 | 3 |
| F05 | same / cross | 3/3 / 3/3 | 3/3 / 3/3 | 3/3 / 3/3 | 3/3 / 3/3 | 3 / 3 |
| F04 | same / cross | 3/3 / 3/3 | 3/3 / 3/3 | 3/3 / 3/3 | 3/3 / 3/3 | 3 / 3 |

In addition: all 18 naive answers retrieved the target text and were technically correct at their core, but the naive answer of F01 cross-chunk r2 invented a claim-dependency chain (P8). Source: report 03 §C, §D ([English translation](../../reports/translated/03_chunk_boundary_full_pipeline_report_en.md)); verbatim excerpts in [`key_evidence/f01_a3_vs_b3.md`](results/key_evidence/f01_a3_vs_b3.md) and [`key_evidence/f01_b2_naive_dependency.md`](results/key_evidence/f01_b2_naive_dependency.md).

## Evidence
- `results/<group>_<condition>_r<n>/`: `actual_chunking.json` (actual chunks and hashes), `chunks.json`, `parsed_extraction.json` (raw extraction records after the official parser), `merged_graph.json`, `natural_query.json` (mix), `natural_naive.json`, `forced_diagnostic.json`, `status.json`.
- `evidence/F0*_evaluation.json`: per-predicate judgments and attribution; `evidence/completed_runs_audit.json`, `cost_summary.json`: hash and cost checks after the runs.
- Local only (`runs/03_chunk_boundary_full_pipeline/original/`): the 18 working directories `storage/`, all `logs/api_*`.

## Analysis and factors ruled out
- F01's missing predicate **first appears in the raw extraction output**; parsing and merging add no further loss. In the cross-chunk condition the entity descriptions still keep part of the case/expert meaning, so the knowledge did not disappear entirely.
- In the cross-chunk condition the claim 4 sentence lies **entirely inside the first chunk**; it is not cut. So it cannot be said that “a relation that needs two chunks to be understood was cut”; more accurately, with this boundary and context arrangement, the representation of the explicit relation is unstable. There is only one clean pair (no truncation on either side): r3.
- All F01 mix answers are correct: text retrieval compensated for what the graph lacked. “The answer is correct” and “the predicate is complete in the graph” are two separate things here.
- In F05 and F04 the cross-chunk condition has more chunks and more repeated tokens than the same-chunk condition, so they are not strictly length-matched.
- Different independent indexes produce the same `source_id` names (e.g. `US9589231B2-chunk-000`) with different content; they must be read together with the run_id / workspace.
- Conclusion: P5′ is marked **to be verified**. In the two reruns the cross-chunk condition kept the predicate 1/3 (11-05) and 3/3 (11-15) times; across the three runs there are 4 clean pairs, 3 of them “kept same-chunk, lost cross-chunk”. See [`docs/REPRODUCIBILITY.md`](../../docs/REPRODUCIBILITY.md).

## Reruns (2026-11-05, 2026-11-15)
- [`results_rerun_20261105/`](results_rerun_20261105/), [`results_rerun_20261115/`](results_rerun_20261115/): 11-05 run by the author on their own machine, 11-15 by Claude Code with the author's authorisation using `run.sh live`; both completed the 18 indexes and the naive follow-up. Complete working directories and logs are only in the local `runs/`.
- Scored with the same rubric, the three runs give: F05 and F04 keep the target predicates under both boundaries; mix retrieves all target text 18/18; mix, naive and forced core answers 18/18; F01's cross-chunk condition keeps the predicate 0/3, 1/3, 3/3; P8 only in the original run. See [`docs/REPRODUCIBILITY.md`](../../docs/REPRODUCIBILITY.md).
- The 11-15 rerun: 117 LLM + 251 embedding calls, ledger estimate CNY 1.34, 2 truncations (F01 same-chunk r1, r2).

## Changes relative to dot's original
- [`RERUN_ADAPTATION_20261105.diff`](RERUN_ADAPTATION_20261105.diff): dot's original → the 11-05 adapted version (the version used in the author's 11-05 run). The differences are in run management only; **extraction and query parameters, prompts, model and frozen conditions are unchanged**:
  1. **timing and session**: the fixed 10-30 UTC times are replaced by the fixed session start and windows of `repro_runtime.py` (queries 102 minutes, hard deadline 120 minutes, watchdog 105 minutes), and the ledger records the session it belongs to;
  2. **interpreter and paths**: the fixed `<TMP>/lightrag-envdiag-20261030/venv/bin/python`, `official_source` and `tiktoken_cache` are replaced by `sys.executable` and package-relative paths; the key path comes from the session configuration;
  3. **entry guards**: `run_pipeline.py` must be given F01/F05/F04 explicitly (M01 is no longer read by default); `naive` runs only when all 18 runs are complete; the watchdog marks a run failed when the subprocess exits non-zero.
- [`PATH_CHANGES.diff`](PATH_CHANGES.diff): path changes made while curating the repository.
- [`CONTENT_CHANGES.diff`](CONTENT_CHANGES.diff): the personal research-interest paragraph removed from the report-generation scripts.
- dot's scripts in `scripts/` contain Chinese comments and a Chinese report template; they are kept as they were.

## Original report
[`reports/original/03_chunk_boundary_full_pipeline_report_zh.md`](../../reports/original/03_chunk_boundary_full_pipeline_report_zh.md) (Chinese; [HTML](../../reports/original/03_chunk_boundary_full_pipeline_report_zh.html), with the round4 pilot and other history snapshots collapsed at the end); [English translation](../../reports/translated/03_chunk_boundary_full_pipeline_report_en.md).
