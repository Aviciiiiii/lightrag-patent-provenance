# 02 Source-field ablation and artificial chunking control (dot's round3, 2026-10-29)

## Purpose
Two control lines:
1. **Source-field ablation**: in 01, Q11's graph facts were “retrieved but misattributed”. What is missing: the source fields, or the claim text?
2. **Artificial chunking control**: with the same text and the same number of calls, only the cut point changes; can the complete technical relation still be extracted from each chunk on its own?

## Setup (differences from 01)
- **No new retrieval, no rebuilt index.** The ablation freezes 01's extended-budget Q11 mix request (API 392: 82 entities, 82 relations, 20 chunks, a 13-entry reference list) and changes only its presentation. Condition names: [`../../docs/NAMING.md`](../../docs/NAMING.md#2-condition-names-inside-the-experiments):
  - **original context** (dot's A): replayed unchanged;
  - **+source fields** (B): `publication_numbers`, `file_path`, `source_id` added to the 82 relations;
  - **+source fields + claim text** (C): B plus the text of claims 1 and 27 of US7991757B2.
  3 runs per condition, in rotating order; all three keep the original reference list (`[1]` is still US10867122B1.txt).
- **Artificial chunking**: the text of claims 26–28 of US7991757B2, 93 tokens, cut into 2 chunks without overlap. **Same chunk** (dot's SAME) cuts between claims 27 and 28; **mid-sentence split** (CROSS) cuts inside the claim 27 sentence, before “machine readable descriptions”. 3 runs per condition, output cap 8192, gleaning=0, LightRAG's official extraction prompt, parsed with the official parser functions.
- Requests are sent directly as OpenAI-compatible HTTP requests, verified character by character against 01's request. 21 LLM calls, 0 embedding calls in total.
- Frozen conditions: [`conditions/`](conditions/), [`evidence/chunk_conditions.json`](evidence/chunk_conditions.json).

## Reproduce
```bash
experiments/02_provenance_ablation_and_chunk_control/run.sh offline
```
Paid rerun: `run.sh live new`, then `prepare-ablation`, `prepare-chunks` (free) → `ablation` → `chunks` (paid, need `LRP_CONFIRM_COSTS=yes`) → `parse` (free). The original run is estimated at CNY 0.15–0.65; in-script hard cap CNY 10. `prepare-ablation` reads 01's API 392 request log, which is kept only in the local `runs/`.

**Prerequisite of the `parse` step**: dot's parser reads the text of 4 LightRAG source files (`_version.py`, `constants.py`, `utils.py`, `operate.py`), executes their unmodified parser functions selectively via AST, and verifies with git that commit, origin and work tree are clean. It reads no non-`.py` file. By decision, **this git verification is kept and the code is not changed**, so a paid rerun reaching `parse` needs a pinned upstream checkout at `runs/LightRAG_PINNED_28ff1b05`. Commands: [docs/SETUP.md §6.1](../../docs/SETUP.md#61-pinned-checkout-for-experiment-02s-parse-step).
Offline replay does not need it, because the scoring scripts use the saved `results/chunk_parsed.json`.

## Expected vs actual
| Measure (3 runs per condition) | original context | +source fields | +source fields + claim text |
|---|---|---|---|
| identifies US7991757B2 correctly | 0/3 | 3/3 | 3/3 |
| completes the claim task with evidence | 0/3 | 0/3 | 3/3 |
| citation numbers conflict with the original mapping | 0/3 | 0/3 | 3/3 |
| affirmative misattribution in the text (e.g. “a different patent family”) | 0/3 | 0/3 | 0/3 |

| Artificial chunking | same chunk | mid-sentence split |
|---|---|---|
| complete technical relation (the module lets a provider supply machine readable descriptions) | 3/3 | 0/3 (only “provide something” remains) |

Source: report 02 §2–§3 ([English translation](../../reports/translated/02_provenance_ablation_and_chunk_control_report_en.md)); verbatim answers and extraction output in [`key_evidence/ablation_source_fields.md`](results/key_evidence/ablation_source_fields.md) and [`key_evidence/same_vs_cross.md`](results/key_evidence/same_vs_cross.md).

## Evidence
- `results/ablation_{A,B,C}_r{1,2,3}.json`: the 9 answers; `results/chunk_{SAME,CROSS}_r*_c*.json`: the 12 raw extractions; `results/chunk_parsed.json`: the official parser's result.
- `conditions/`: the complete requests of the three conditions, field-level diffs, and a check of the `source_id` of each of the 82 relations.
- `evidence/ablation_evaluation.json`, `chunk_evaluation.json`: dot's scoring (criteria written into `conditions/condition_manifest.json` before the calls).
- Local only: `runs/02_provenance_ablation_and_chunk_control/original/logs/`.

## Analysis and factors ruled out
- “+source fields” restores the document attribution, but the three fields were added together, so **their individual contributions cannot be separated**, and the context length changed as well.
- 01's affirmative misattribution was reproduced 0/3 times in the “original context” condition, so it **cannot** be said that adding source fields “fixed” that error. What can be said is that with sources the model identifies the right patent.
- The citation-number conflict of condition C comes from the experiment design (the reference list was not updated, to keep the ablation pure) and does not indicate a failure rate of normal end-to-end citation (P9, experiment code).
- The mid-sentence split is an artificially built 93-token stress test, unlike 01's natural 1200/100 chunking. In 01 the genuinely cross-chunk claim 1/27 relation was kept. The mid-sentence condition still keeps some nodes such as the module and the provider, so the facts did not disappear entirely. No joint cross-chunk extraction or downstream QA was run, so it cannot be claimed that downstream steps could not recover the relation.
- The selective execution of the parser was checked for equivalence only on the saved groups of 01's API 191 (report 02 §5; P10).

## Reruns (2026-11-05, 2026-11-15)
- [`results_rerun_20261105/`](results_rerun_20261105/), [`results_rerun_20261115/`](results_rerun_20261115/): 11-05 run by the author on their own machine, 11-15 by Claude Code with the author's authorisation using `run.sh live`; both with the same model and parameters. The frozen conditions were regenerated by the prepare steps and are identical to the original (only the timestamps in the manifest differ).
- Scored with the same rubric ([`docs/SCORING_RUBRIC.md`](../../docs/SCORING_RUBRIC.md)), the three runs give identical results: right patent 0/3, 3/3, 3/3; claim task completed with evidence 0/3, 0/3, 3/3; citation conflict in condition C 3/3; mid-sentence split 0/3, same chunk 3/3. See [`docs/REPRODUCIBILITY.md`](../../docs/REPRODUCIBILITY.md).

## Changes relative to dot's original
- [`RERUN_ADAPTATION_20261105.diff`](RERUN_ADAPTATION_20261105.diff): timing and session, the key path, and letting both parser scripts share one pinned git checkout with git verification; conditions, prompts and parameters unchanged.
- [`PATH_CHANGES.diff`](PATH_CHANGES.diff): path mapping; the pinned checkout defaults to `runs/LightRAG_PINNED_28ff1b05`.
- [`CONTENT_CHANGES.diff`](CONTENT_CHANGES.diff): the personal research-interest paragraph removed from the report-generation script.
- dot's scripts in `scripts/` contain Chinese comments and a Chinese report template; they are kept as they were.

## Original report
[`reports/original/02_provenance_ablation_and_chunk_control_report_zh.md`](../../reports/original/02_provenance_ablation_and_chunk_control_report_zh.md) (Chinese; [HTML](../../reports/original/02_provenance_ablation_and_chunk_control_report_zh.html)); [English translation](../../reports/translated/02_provenance_ablation_and_chunk_control_report_en.md).
