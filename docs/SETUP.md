# Setup and running

This document merges dot's two tutorials (the original and a later “startup fix” revision; the revision prevails; both are kept by the author and not published), adapted to this repository's layout and commands, plus the parts of dot's environment-diagnosis report that matter for reproduction. All commands run from the repository root.

## 0. Three routes

| Route | What it does | API calls? | Needs |
|---|---|---|---|
| **Read results** (default for demos) | read `experiments/*/results/`, `key_evidence/`, `reports/` | no | the git repository only |
| **Offline replay** (the tutorials' “H route”) | dot's offline scripts recompute scores and rebuild reports from the saved results; the output is compared with the committed originals | no | the local `runs/` folder (not in git, see §3) |
| **Real rerun** (the tutorials' “N route”) | calls the LLM/embedding API again in a fresh `runs/rerun_*` directory; committed results are never overwritten | **yes (paid)** | `.env` + explicit cost confirmation |

The tutorials originally used three “N” copies plus one offline copy of the evidence package (`LightRAG_NEW_A/B/C`, `LightRAG_OFFLINE`). Here there is one copy of the code; `run.sh live new` creates a separate directory for each rerun, which gives the same isolation.

## 1. Environment

- Python **3.10** (original runs: 3.10.6; the author's conda environment `lightrag` is 3.10.22 and passes the smoke test).
- All dependencies are pinned in [`requirements.txt`](../requirements.txt), taken from the isolated environment dot built for experiment 03; it contains `lightrag-hku==1.5.7`. All its `.py` files are byte-identical to upstream commit `28ff1b05`, so this repository does not vendor the LightRAG source.
- Plotting additionally needs `requirements-figures.txt` (only for `tools/plot_merged_nodes.py`).

```bash
conda create -n lightrag-repro python=3.10 -y
```

```bash
conda activate lightrag-repro
```

```bash
pip install -r requirements.txt
```

### 1.1 Imports that stall for minutes

In rounds three and four, `import lightrag` sometimes hung for a long time. dot's diagnosis (2026-10-30) found:

- Many dependency files in the old virtual environment were in macOS's **dataless** state (content not stored locally, materialised on first read); `ls -lO` shows the `dataless` flag. Each such `.pyc`/`.py` took seconds to read: `import networkx` had not finished after 75 seconds, and a full LightRAG import took about 58 seconds.
- Pointing `PYTHONPYCACHEPREFIX` at an empty directory brought `import networkx` down to 0.29 seconds; in a fresh virtual environment on a local disk a full LightRAG import took about 7 seconds the first time and 0.3 seconds afterwards.
- What made the files dataless (sync, storage optimisation, cleanup) was **not determined**; the report does not attribute it to iCloud.

Recommendation: create the virtual environment in a local directory that is not synced or “storage-optimised”. If imports are unusually slow, run `python -X importtime -c "import lightrag" 2>&1 | tail` and check site-packages with `ls -lO`.

### 1.2 API key

```bash
cp .env.example .env
```

Put a SiliconFlow (or other OpenAI-compatible) key into `.env`, which is ignored by git. The original runs read the key from an external disk (`<EXTERNAL_DISK>/LightRAG/secrets/.env`); the scripts in this repository read `.env` in the repository root, or the file named by the environment variable `LRP_ENV_FILE`. Only real reruns need it.

## 2. Smoke test (no API calls)

```bash
python tools/smoke_check.py
```

It checks the Python and LightRAG versions, compares 7 LightRAG source files with the SHA256 of upstream `28ff1b05`, checks that every input of every experiment is found through `paths.py`, that all scripts compile and the session module loads (no session is created), that `.env` has the required keys (values are not shown), and that the tokenizer works offline. Two deterministic checks are added:

- experiment 03: dot's custom chunker re-chunks the 3 groups × 2 conditions and the 15 saved chunks match by SHA256;
- experiment 01: the local index is readable and the graph has 612 nodes / 994 edges.

In a fresh clone, the local-only files of `runs/` and `.env` are reported as WARN, not FAIL. A single experiment: `experiments/0X_*/run.sh check`.

## 3. Local files (`runs/`)

Experiment 01's original index is committed (`experiments/01_baseline_index_qa/index/`). The other complete LightRAG working directories, all API logs and the tokenizer cache are not in git (about 220 MB on the author's machine, including a local copy of the index). The author rebuilds them from dot's evidence package, which is not published:

```bash
python tools/setup_local_runs.py --a <path>/LightRAG_NEW_A --b <path>/LightRAG_NEW_B --c <path>/LightRAG_NEW_C
```

`--check` only compares, without copying. Which copy holds which round's original and rerun results: [NAMING.md](NAMING.md).

## 4. Offline replay (no API calls)

```bash
experiments/01_baseline_index_qa/run.sh offline
```

`offline` copies the experiment's saved results to `runs/offline_<experiment>_<time>/`, runs dot's offline scripts there, and lists the files that differ from the committed originals. Result on the author's machine, 2026-11-13: all four experiments replay completely; every difference is a generation timestamp, a file-path field, or the byte count and hash that change with them. The report text matches the original report except for timestamps and the removed personal paragraph.

| Experiment | dot's scripts that run (tutorial H route) | Time |
|---|---|---|
| 01 | `collect_query_evidence.py` → `build_report.py` | seconds |
| 02 | `evaluate_ablation.py` → `evaluate_chunks.py` → `build_report.py` | seconds |
| 03 | `audit_completed_runs.py` → `build_final_report.py` | seconds |
| 04 | `build_inventory.py` → `validate_reviews.py --require-complete` → `source_mapping_audit.py` → `check_original_documents.py` → `build_report.py` | < 1 minute |

Note (from the tutorials): these scoring and report scripts contain dot's fixed judgments, written after reading the original answers. They can only replay the historical results and **cannot** score the output of a new rerun.

## 5. Live reproduction of “the source does not reach the context” (no API calls)

```bash
python tools/demo_context_provenance.py --replay-answer --md runs/demo.md
```

On a copy of experiment 01's original index, it reruns LightRAG's own `mix` query pipeline (`aquery_data` + `only_need_context=True`) with the parameters of the original Q11 call. The LLM function is replaced by a stub that raises if called. Query vectors come from `experiments/01_baseline_index_qa/evidence/q11_query_vectors_bge-m3.json`: the bge-m3 vectors of the original Q11's three query texts, computed on 2026-11-15 by `tools/compute_q11_query_vectors.py` with one API call, inputs identical to the original log. The demo therefore makes 0 API calls, its output is deterministic, and its retrieval is identical to the original Q11. `--proxy-vector` keeps the older stand-in mode (one entity's own vector as the query vector). `--lang zh` writes the Markdown in Chinese. More: [FAQ](FAQ.md#the-demo-calls-no-embedding-api-where-do-the-query-vectors-come-from-and-is-the-retrieval-the-same-as-in-the-original-run).

The index it needs is committed in [`experiments/01_baseline_index_qa/index/`](../experiments/01_baseline_index_qa/index/README.md) (the original index of 2026-10-29, 16 MB, with `SHA256SUMS.txt`); a copy in `runs/01_baseline_index_qa/original/storage_full/` is used only if the committed one is absent. The script copies it to `runs/demo_context/` and never writes into it.

## 6. Real rerun (paid; confirm first)

Per experiment:

```bash
experiments/01_baseline_index_qa/run.sh live new
```

then run the steps in order, checking the output of each before the next (paid steps need explicit confirmation):

```bash
LRP_CONFIRM_COSTS=yes experiments/01_baseline_index_qa/run.sh live preflight
```

| Experiment | Steps (in order) | Original calls and time | Original cost estimate (not an invoice) | In-script hard cap |
|---|---|---|---|---|
| 01 | `preflight` → `smoke` → `full` → `probe` → `budget` | 95 LLM + 297 embedding; about 31 minutes of API time | CNY 1.56–1.77 | CNY 10 |
| 02 | `prepare-ablation`, `prepare-chunks` (free) → `ablation` → `chunks` → `parse` (free) | 21 LLM; about 25 minutes including preparation | CNY 0.15–0.65 | CNY 10 |
| 03 | `F01` → `F05` → `F04` → `naive` | 117 LLM + 247 embedding; about 19 minutes | CNY 1.08–1.33 | CNY 4 |
| 04 | none (read-only audit) | 0 | CNY 0 | — |

Cost source: the cost section of each original report ([01](../reports/translated/01_baseline_index_qa_report_en.md), [02](../reports/translated/02_provenance_ablation_and_chunk_control_report_en.md), [03](../reports/translated/03_chunk_boundary_full_pipeline_report_en.md)), estimated at SiliconFlow's public prices at the time (input CNY 2/M, output CNY 8/M, cached input CNY 0.04/M, bge-m3 free). The author's second run on 2026-11-05: experiment 01 ledger estimate CNY 1.78.

dot's scripts have built-in run guards, kept unchanged:

- **Fixed time window**: the first paid step writes the start time into `config/repro_session.json` of the rerun directory. The query window is 60 minutes (102 minutes for experiment 03) and the hard deadline 120 minutes. After that the scripts refuse to continue and do not restart the clock; to run again, run `live new` again.
- **Cost ledger**: before every call the maximum cost is reserved; the script stops at the hard cap. The steps of one experiment must run one after another.
- **Experiment 02 `parse`**: uses dot's “selective execution of the official parser functions” and keeps dot's git verification (commit = `28ff1b05`, origin = the official repository, clean work tree, 4 source files byte-identical to git). It needs an upstream checkout, see §6.1.
- **Experiment 03 `naive`** must run after all 18 indexes are complete; `run_pipeline.py` must be given the group names (otherwise it also reads M01, which is not part of this run).

New output must be scored anew; dot's historical scoring scripts do not apply. Follow §6.0: score with `tools/score_runs.py`, then review.

### 6.0 Complete workflow of a new rerun

Below, `<L>` is the date label of the rerun (`YYYYMMDD`, the same for all three experiments) and `<UTC01>`, `<UTC02>`, `<UTC03>` are the directory timestamps printed by `live new` (for example `20261201T081500Z`). Paid steps need `LRP_CONFIRM_COSTS=yes`. Check the output of each step before the next; if a paid step fails, do not rerun it automatically; read the record from `summarize_rerun.py` first.

**0. Preparation** (keep the key file outside the repository and point to it with the environment variable)

```bash
conda activate lightrag
export LRP_ENV_FILE=<absolute path of the .env file>
python tools/smoke_check.py
```

**1. Experiment 01** (about 31 minutes, original estimate CNY 1.56–1.77)

```bash
experiments/01_baseline_index_qa/run.sh live new
LRP_CONFIRM_COSTS=yes experiments/01_baseline_index_qa/run.sh live preflight
LRP_CONFIRM_COSTS=yes experiments/01_baseline_index_qa/run.sh live smoke
LRP_CONFIRM_COSTS=yes experiments/01_baseline_index_qa/run.sh live full
LRP_CONFIRM_COSTS=yes experiments/01_baseline_index_qa/run.sh live probe
LRP_CONFIRM_COSTS=yes experiments/01_baseline_index_qa/run.sh live budget
```

**2. Experiment 02** (about 25 minutes, original estimate CNY 0.15–0.65; `parse` needs the checkout of §6.1)

```bash
experiments/02_provenance_ablation_and_chunk_control/run.sh live new
experiments/02_provenance_ablation_and_chunk_control/run.sh live prepare-ablation
experiments/02_provenance_ablation_and_chunk_control/run.sh live prepare-chunks
LRP_CONFIRM_COSTS=yes experiments/02_provenance_ablation_and_chunk_control/run.sh live ablation
LRP_CONFIRM_COSTS=yes experiments/02_provenance_ablation_and_chunk_control/run.sh live chunks
experiments/02_provenance_ablation_and_chunk_control/run.sh live parse
```

**3. Experiment 03** (about 19 minutes, original estimate CNY 1.08–1.33; `naive` must run last)

```bash
experiments/03_chunk_boundary_full_pipeline/run.sh live new
LRP_CONFIRM_COSTS=yes experiments/03_chunk_boundary_full_pipeline/run.sh live F01
LRP_CONFIRM_COSTS=yes experiments/03_chunk_boundary_full_pipeline/run.sh live F05
LRP_CONFIRM_COSTS=yes experiments/03_chunk_boundary_full_pipeline/run.sh live F04
LRP_CONFIRM_COSTS=yes experiments/03_chunk_boundary_full_pipeline/run.sh live naive
```

**4. Run record and rough check** (no API calls; can also run while the rerun is in progress, with only the experiments that exist)

```bash
python tools/summarize_rerun.py --label <L> \
  --exp01 runs/rerun_01_baseline_index_qa_<UTC01> \
  --exp02 runs/rerun_02_provenance_ablation_and_chunk_control_<UTC02> \
  --exp03 runs/rerun_03_chunk_boundary_full_pipeline_<UTC03> \
  --operator 'the author, on their own machine' \
  --out docs/RERUN_<L>_CHECK.md
```

It lists the steps run, start and end times, models and parameters, numbers of LLM and embedding calls, the ledger total, every call with `finish_reason=length`, failed or missing steps, and a string-level rough check of the phenomena shown in the README. It is a run record, not scoring. `--operator` states who ran it; without `--out` it only prints. `--lang zh` writes Chinese (for local reading).

**5. Import into the repository** (sanitised; copies only `results/`, `evidence/`, `conditions/` and writes a `RUN_RECORD.md`; logs and working directories stay in `runs/`)

```bash
experiments/01_baseline_index_qa/run.sh import runs/rerun_01_baseline_index_qa_<UTC01> --label <L> --operator 'the author, on their own machine'
experiments/02_provenance_ablation_and_chunk_control/run.sh import runs/rerun_02_provenance_ablation_and_chunk_control_<UTC02> --label <L> --operator 'the author, on their own machine'
experiments/03_chunk_boundary_full_pipeline/run.sh import runs/rerun_03_chunk_boundary_full_pipeline_<UTC03> --label <L> --operator 'the author, on their own machine'
```

Results go to `experiments/<experiment>/results_rerun_<L>/`. Without `--label` the UTC date in the directory name is used; the three experiments may span two dates, so pass the same `<L>` explicitly. Local paths are replaced by placeholders during import; if the value of any key in the `.env` file appears in a copied file, the whole import is aborted (without `LRP_ENV_FILE` or `.env` this scan is skipped, with a warning). An existing target directory is never overwritten.

**6. Scoring** (no API calls)

```bash
python tools/score_runs.py <L>
```

This writes `docs/scoring/scores_<L>.json` and lists the judgments whose rule value differs from the original run (S10, truncation, is a logged fact and is not listed). Read the answer or merged graph behind each of them, record the conclusion in a review file, and run the command again:

- a review by the author goes into `docs/scoring/human_review_<L>.json`; the item is then marked “reviewed by the author”;
- a review by Claude Code goes into `docs/scoring/claude_review_<L>.json`; the item is marked “reviewed by Claude Code, pending human review”; items in neither file are marked “rule only, not reviewed item by item”.

A human review takes precedence. Formats:

```json
{"S9:F01_B_r1": {"value": true, "note_zh": "<original note, if written in Chinese>", "note_en": "edges[9] of merged_graph.json records ...", "review_language": "zh", "date": "2026-12-01"}}
```

```json
{"S9:F01_B_r1": {"value": true, "note": "Claude Code read the merged graph: ..."}}
```

**7. Comparison table** (no API calls)

```bash
python tools/build_reproducibility.py --write docs/REPRODUCIBILITY.md
```

By default it includes `original` and every scored rerun (with `results_rerun_<L>/` and `scores_<L>.json`) and replaces only the tables between the two `<!-- BEGIN/END tables generated … -->` markers in `REPRODUCIBILITY.md`. Experiment 01's request log is looked up in `runs/01_baseline_index_qa/rerun_<L>/logs` and `runs/rerun_01_baseline_index_qa_<L>T*/logs`; if the date of `live new` differs from `<L>`, add `--extra-logs runs/rerun_01_baseline_index_qa_<UTC01>/logs`. The text outside the tables (“Summary” in REPRODUCIBILITY.md, the Reproducibility section of the README) must be updated by hand.

**8. Checks**

```bash
python tools/smoke_check.py
python tools/check_links.py
python tools/check_translations.py --pairs
```

#### What a rerun directory contains

`run.sh live new` creates `runs/rerun_<experiment>_<UTC time>/` (all of `runs/` is outside git); every later step writes there, and committed results are never overwritten. The layout follows dot's round folders:

| Location | Content | Experiments |
|---|---|---|
| `config/repro_session.json` (and `.lock`) | **session file**: group, fixed start time, path of the key file (the absolute path of `.env`, not the key). It defines the time window | 01, 02, 03 |
| `results/cost_ledger.json` | **cost ledger**: per call the stage, kind (llm/embedding), start and end time, returned model name, `finish_reason`, usage, estimated cost and running total | 01, 02, 03 |
| `logs/api_NNNN_request.json` / `_response.json` | **request / response log**: the complete messages and parameters sent to the model (without Authorization) and the model's complete answer. 02 and 03 also keep `_provider_response.json` (the provider's raw JSON) | 01, 02, 03 |
| `logs/api_NNNN_embedding.json` | input texts, usage and shape of embedding calls | 01 |
| `logs/F0x_pipeline.log`, `naive_followup.log` | standard output of subprocesses | 03 |
| other files in `results/` | **results**: 01 `preflight.json`, `smoke_*`, `full_Q*_{naive,mix}.json`, `supplement_budget_*.json`, `full_graph.json`, `*_run_status.json`; 02 `ablation_*_r*.json`, `chunk_*_r*_c*.json`, `chunk_parsed.json`; 03 `<group>_<condition>_r<n>/` (chunking, parsing, merged graph, answers), `run_status_F0x.json`, `naive_followup_status.json` | 01, 02, 03 |
| `evidence/` | runtime configuration (`public_runtime_config.json`), parameter snapshot (01: `full_settings.json`), rank probe and others | 01, 02, 03 |
| `conditions/` | frozen conditions (02: generated by the prepare steps; 03: copied from the repository) | 02, 03 |
| `storage_full/`, `storage_smoke/` (01), `storage/<run_id>/` (03) | **LightRAG working directories**: graph (GraphML), vector databases, KV stores (including `kv_store_llm_response_cache.json`) | 01, 03 |

### 6.1 Pinned checkout for experiment 02's parse step

**Only a paid rerun of experiment 02 needs it.** The `parse` step makes no API call itself, but it parses the extraction responses produced by the preceding paid step `chunks`, so it only occurs in a paid rerun. The smoke test, offline replay (`run.sh offline` uses the saved `results/chunk_parsed.json`), the live demo, and experiments 01, 03 and 04 do not need it.

```bash
git clone https://github.com/HKUDS/LightRAG.git runs/LightRAG_PINNED_28ff1b05
```

```bash
git -C runs/LightRAG_PINNED_28ff1b05 checkout --detach 28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c
```

The clone URL must be the official one above (the verification checks origin), and no file in the checkout may be changed (the verification requires a clean work tree). `runs/` is ignored by git. An existing identical checkout can be used instead of cloning:

```bash
export LIGHTRAG_REPRO_SOURCE=<absolute path of the existing checkout>
```

Verified on 2026-11-13 with an existing checkout on the author's machine: dot's `verify_source()` passes in the new layout; commit, origin, work tree and the 4 source files all check out.

## 7. Can the LLM cache make reruns fast and consistent?

Experiment 01's original index contains `kv_store_llm_response_cache.json` (47 extraction, 26 query, 11 keyword and 2 summary entries). Measured on 2026-11-15:

- **Query replay (measured)**: with the saved bge-m3 query vectors (§5) and an LLM stub that raises, `aquery_llm` was called for Q11 (extended budget, mix) with the original parameters. Keywords and answer both came from the cache; no LLM was called. The answer is identical to the original API 392 answer. Retrieved entities, relations and chunks are identical to the original; the context has the same lines, 33 of them in a different order ([FAQ](FAQ.md#why-are-33-context-lines-in-a-different-order)).
- **What a cache hit shows**: question, mode, budgets, keywords and user_prompt are the same as in the original call (in v1.5.7 they make up the query-cache key, see `compute_args_hash` in `kg_query`), and no LLM was called.
- **What it does not show**: (1) that the model would answer the same today, because the answer is retrieved, not regenerated; (2) that the retrieved context is the same, because the context is not part of the cache key and has to be compared separately (done above).
- **Other questions**: query vectors were saved only for Q11. Replaying other questions needs new embedding calls (LightRAG does not cache embeddings by default).
- **Rebuilding the index**: the 47 cached extractions save the LLM calls for most chunks, but the truncated extraction of API 191 is not cached; that chunk would be extracted again and the result may differ.

An answer replayed from the cache only re-creates the original answer; it is **not a new independent run**. The independent reruns are in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).
