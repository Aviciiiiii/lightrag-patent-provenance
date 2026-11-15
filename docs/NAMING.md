# Old names → new names

The original material has three unrelated sets of “A/B/C”, and folder numbers and report titles do not match. The repository's documents (README, experiment READMEs, FAQ) **use only the new names in the left column**; original file names, dot's scripts and JSON fields keep the old names. Use these tables to translate.

## 1. Experiments

| New name | Original folder | Name in dot's tutorials | Original report title / file | Copy holding the original results | Copy holding the 2026-11-05 rerun |
|---|---|---|---|---|---|
| **01_baseline_index_qa** (baseline index and QA) | `round2/` | group A | “second-round experiment report”, `LightRAG实验报告/…_zh (1).html` | `LightRAG_NEW_B`, `LightRAG_NEW_C` (identical) | `LightRAG_NEW_A` |
| **02_provenance_ablation_and_chunk_control** (source-field ablation and artificial chunking control) | `round3/` | group B | “third-round control experiments”, `…_zh (2).html` | `LightRAG_NEW_A`, `LightRAG_NEW_C` | `LightRAG_NEW_B` |
| **03_chunk_boundary_full_pipeline** (chunk boundary, full pipeline) | `round4_full_20261030/` | group C | titled “**third-round** Chunk Boundary Ablation complete-pipeline supplementary report”, `…_zh (4).html` | `LightRAG_NEW_A`, `LightRAG_NEW_B` | `LightRAG_NEW_C` |
| **04_merged_node_audit** (merged-node audit) | `round2_multisource_audit/` | group D | “second round: cross-patent node sources and semantic audit”, `LightRAG_round2_multisource_node_audit_zh.html` | identical in all three | none (read-only audit, no rerun) |
| data/round1 (data preparation and chunk pre-check) | package root `scripts/ results/ evidence/ logs/ report/` | — | “time-limited validation record” (round one) | identical in all three | none |
| (local only) round4 pilot | `round4/` | — | “fourth round: strict chunk pre-check and minimal extraction control” (partly completed) | identical in all three | none |
| (local only) environment diagnosis | `env_diagnostics_20261030/` | — | “environment diagnosis and isolated recovery” | identical in all three | none |

The folders `LightRAG_NEW_A/B/C` are **not three experiments** but three copies of the same evidence package; each was used to rerun one round (last column).

## 2. Condition names inside the experiments

| Experiment | Original name | New name | Meaning |
|---|---|---|---|
| 02 source-field ablation | condition A | original context / `orig-context` | replays the request that round two sent to the model for Q11 (API 392) unchanged |
| 02 | condition B | +source fields / `+provenance` | adds `publication_numbers`, `file_path`, `source_id` to the 82 relations |
| 02 | condition C | +source fields + claim text / `+provenance+claims` | B plus the original text of claims 1 and 27 of US7991757B2 |
| 02 artificial chunking | SAME | same chunk / `same-chunk` | boundary between claims 27 and 28 |
| 02 artificial chunking | CROSS | mid-sentence split / `split-in-sentence` | boundary inside the claim 27 sentence |
| 03 | condition A | same-chunk boundary / `same-chunk` | a chunking in which the target evidence lies in one chunk |
| 03 | condition B | cross-chunk boundary / `cross-chunk` | a chunking in which no chunk contains both kinds of target evidence |
| 03 | F01 / F05 / F04 | unchanged | the three patents: US9589231B2 / US8069128B2 / US8509827B2 |
| 03 | M01 | unchanged | an earlier trimmed US7991757B2 control (part of the round4 pilot, not one of the 18 runs) |
| 01 | Q01–Q10, Q11 | unchanged | Q11 is the natural cross-chunk supplementary question (`evidence/optional_question11.json`) |

## 3. Problem IDs

Problem IDs P1–P12 are defined in the top-level [README](../README.md#problem-overview) and in [AUDIT.md](AUDIT.md).

## 4. Path placeholders

Every text copied into the repository went through [`tools/sanitize_paths.py`](../tools/sanitize_paths.py); local absolute paths are replaced by:

| Placeholder | Meaning |
|---|---|
| `<DOT_WORKDIR>` | dot's original working directory (`<HOME>/Documents/Codex/2026-10-29/task/lightrag_patent_20261029`) |
| `<ORIG_COPY>/LightRAG_…` | the copies of the evidence package in the author's Downloads folder (`LightRAG_NEW_A/B/C`, `LightRAG_OFFLINE` and others) |
| `<HOME>` | the user's home directory |
| `<EXTERNAL_DISK>` | the external disk holding the private `.env` |
| `<TMP>` | the macOS system temporary directory (dot built an isolated venv there: `<TMP>/lightrag-envdiag-20261030`) |
| `<VAR_FOLDERS>` | the macOS per-user temporary directory |
| `<DOWNLOADS>` | the author's Downloads folder, as referred to in the documents |

## 5. Same-name folders in Downloads (compared 2026-11-12)

The repository was built only from the material in `lightRAG_exp/`. Several folders with the same names exist in Downloads; a file-by-file comparison (ignoring `.DS_Store` and `__pycache__`) gives:

| Folder | Relation to `lightRAG_exp/` |
|---|---|
| `<DOWNLOADS>/LightRAG_NEW_A`, `_B`, `_C` | **identical file by file** to `lightRAG_exp/LightRAG_NEW_A/B/C` (`diff -rq` prints nothing). `lightRAG_exp` is a complete copy of them. |
| `<DOWNLOADS>/LightRAG_reproduction_bundle_20261104/lightrag_patent_20261029/` | dot's original combined package (the tutorials call it “the original, read only”). Matches the **original-results side** of each NEW copy. Also contains `audit_notes/`, `historical_variants/` (notes and checksums of earlier partial packages) and `tutorial/`. |
| `<DOWNLOADS>/LightRAG_OFFLINE_WORK_20261104` | identical to `lightrag_patent_20261029/` in the combined package above (also original results). |
| `<DOWNLOADS>/LightRAG_OFFLINE` | the copy for the tutorials' offline route H. Compared with the combined package, 15 files differ, all **regenerated** offline by the author on 2026-11-05: report HTML, `report_summary.json` and audit summary JSON. The regenerated round2, round3 and round4_full reports differ from the originals **only in their generation timestamps** (and the “minutes elapsed” computed from them), which shows that these reports can be rebuilt offline from the saved results. |
| `<DOWNLOADS>/LightRAG_PINNED_28ff1b05` | a git checkout of upstream LightRAG, HEAD = `28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c`, origin = the official repository, clean work tree. Used only for the git verification of experiment 02's parser (see the experiment 02 README). |
| scattered files such as `<DOWNLOADS>/LightRAG_patent_provenance_report_zh*.html` | repeated downloads of the reports, matched one by one in [reports/README.md](../reports/README.md). |
