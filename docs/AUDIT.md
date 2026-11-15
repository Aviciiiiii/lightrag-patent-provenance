# Audit report (inventory and audit of the original material, 2026-11-12, with later additions)

Prepared by Claude Code for the author. Date of the main audit: 2026-11-12. Scope: all material in `lightRAG_exp/`, read only; nothing was written into `lightRAG_exp/` and no paid API was called.
Network use was limited to three things: `git ls-remote` for the upstream tags, downloading upstream `operate.py`/`prompt.py`/`_version.py` of `main` to a scratch directory for comparison, and a search of GitHub issues.

---

## 0. Conclusions first (5 points)

1. **A/B/C are not three experiments but three copies of the same “full evidence package”.** Each contains round1–round4, the merged-node audit, the data and the LightRAG source. In each copy one round was **rerun by the author on 2026-11-05**: A → round2, B → round3, C → round4_full. dot's original (10-29/10-30) results are in the other two copies, which are pairwise identical. The reports correspond to the original results.
2. **“The four experiments” are groups A/B/C/D of the tutorials** = round2 (baseline index + QA) / round3 (source-field ablation + artificial chunking) / round4_full_20261030 (chunk boundary, full pipeline) / round2_multisource_audit (merged-node audit). The audit reuses round2's original graph. Three supporting items are outside the four: round1 (data + chunk pre-check, no LLM call), the round4 pilot (partly completed), env_diagnostics (environment diagnosis).
3. **The LightRAG source was not modified.** In the 6 source copies (3 × `src/LightRAG-v1.5.7` + 3 × `round4/runtime_source`), `lightrag/` is byte-identical to the official archive dot saved, which corresponds to upstream tag `v1.5.7` = commit `28ff1b05…`. All `.py` files of `lightrag-hku==1.5.7` installed with pip in the author's conda environment `lightrag` are byte-identical too (differences only in documentation, sample data and web-UI build output). → The repository can pin the pip version; no patch is needed.
4. **dot's glue code passed the provenance information correctly**: documents were inserted with `ids` = publication number and `file_paths` = `<number>.txt`, and the first line of each document states the number; queries use the official `aquery_llm` with `include_references=True`, saving the answer and the structured evidence of the same call. `source_id` and `file_path` exist on entities and relations, `full_doc_id` on chunks.
5. **The core problem (the Q11 misattribution) arises between “retrieval result → LLM prompt”, not in storage**: when v1.5.7 assembles the KG context it removes `file_path` from entities and relations (`operate.py:5462–5494`; an intentional change, see upstream commit [`d3fde609`](https://github.com/HKUDS/LightRAG/commit/d3fde60938c7e14f5e5dff07d4fbd4196e86cbce) “remove file_path and created_at from context”, reason not stated), and the reference list is built only from chunks (`operate.py:5813–5829`). Which graph fact came from which patent is therefore in the structured result but not in the prompt the model sees. This is a **design trade-off of LightRAG** (token saving, citation granularity at chunk level) and is unchanged in upstream `main` and the newest release (checked again on 2026-11-15, see addition 10). dot's user_prompt (“give the publication number only when it appears in the evidence”) amplifies the effect.

---

## a. File inventory

### Top level
| Path | Size | Nature |
|---|---|---|
| `LightRAG_NEW_A/` | 167M | full evidence-package copy; round2 rerun on 11-05 |
| `LightRAG_NEW_B/` | 166M | full evidence-package copy; round3 rerun on 11-05 |
| `LightRAG_NEW_C/` | 164M | full evidence-package copy; round4_full rerun on 11-05 |
| `LightRAG_四组实验_Mac双路径实操教程.html` (“four experiments, two routes on a Mac, practical tutorial”) | 36K | dot's tutorial (original) |
| `LightRAG_四组实验_Mac双路径实操教程_启动修正版.html` (same, “startup fix” revision) | 36K | dot's tutorial (11-05 revision) |
| `LightRAG实验报告/` (“LightRAG experiment reports”) | 652K | 4 HTML reports (see the mapping) |

Also: `LightRAG_NEW_A/B/C` under `<DOWNLOADS>/` are identical file by file to those in `lightRAG_exp/` (`diff -rq` prints nothing), so `lightRAG_exp` is a complete copy. The tutorials and B's parser scripts also depend on two locations outside `lightRAG_exp/`: `<DOWNLOADS>/LightRAG_PINNED_28ff1b05` (an upstream git checkout, 35M) and `<EXTERNAL_DISK>/LightRAG/secrets/.env` (the key).

### Internal structure of each copy (B shown; A and C are the same)
| Folder | Size | Content | Nature |
|---|---|---|---|
| `src/LightRAG-v1.5.7/` | 8.5M | upstream source (only the `lightrag/` package + LICENSE/README/pyproject) | **LightRAG source copy** |
| `round4/runtime_source/` | 8.5M | a second copy of the same | **LightRAG source copy** |
| `evidence/official_LightRAG_v1.5.7_source_sanitized.tar.gz` | 8.6M | archive of the complete upstream repository | **LightRAG source copy** |
| `tiktoken_cache/` | 3.4M | o200k_base vocabulary cache | dependency cache |
| `data/` | 18M | the 20 patents' `documents/*.txt`, `claims/*.json`, the first 100 raw Dis2Pat rows (6.4M), `source_checks/*.html` (20 Google Patents pages), manifests and checks | input data |
| `scripts/`, `results/`, `report/`, `logs/`, `evidence/` (root) | ~9M | round1: data fetching, chunk pre-check, question building | dot's scripts + output |
| `round2/` | 28M | `scripts/` (7), `storage_smoke/`, `storage_full/` (16M, LightRAG working directory), `logs/api_*` (4.5M), `results/`, `evidence/`, `report/` | dot's scripts + **run output** |
| `round3/` | 3.6M | `scripts/` (13), `conditions/`, `logs/`, `results/`, `evidence/`, `report/` | dot's scripts + run output |
| `round4/` | 11M | pilot: `scripts/` (14), `runtime_source/`, `logs/`, `results/`, `report/` | dot's scripts + run output |
| `round4_full_20261030/` | 71M | `scripts/` (19), `storage/` (15M, 18 working directories), `logs/` (50M), `results/`, `evidence/`, `conditions/`, `delivery_split_20261030/`, `report/` | dot's scripts + **run output** |
| `round2_multisource_audit/` | 9.9M | `source_mapping_audit.py`, `scripts/` (8), `dossiers/`, `reviews/`, `evidence/`, `report/`, SHA256SUMS | dot's scripts + audit output (no API) |
| `env_diagnostics_20261030/` | 3.5M | environment-diagnosis scripts, logs, smoke index | dot's scripts + output |
| `config/repro_session.{json,sh,lock}` | 8K | session written by the author's 11-05 rerun (contains absolute paths) | local run state |
| `START_HERE.txt`, `README.txt`, `MANIFEST.json`, `PACKAGE_*.json`, `artifact_*.json`, `verify_package_contents.py` | — | packaging notes and checks | dot's packaging metadata |

Run output (LightRAG working directories):
- `round2/storage_full/patent_r2_full/`: `graph_chunk_entity_relation.graphml`, `kv_store_*.json` (including `kv_store_llm_response_cache.json`: 47 extract / 26 query / 11 keywords / 2 summary), `vdb_{chunks,entities,relationships}.json`
- `round4_full_20261030/storage/F0x_{A,B}_r{1,2,3}/patent_r4_*/`: 18 sets with the same structure
- `round2/storage_smoke/`, `env_diagnostics_20261030/storage_smoke_network1/`: smoke tests

**No single file is larger than 20MB** (largest: source archive 8.6M, `vdb_relationships.json` 8.0M, raw Dis2Pat rows 6.4M).

---

## b. Mapping

“Original” = dot's run of 10-29/30 (the reports correspond to it); “rerun” = the author's run of 11-05.

| Experiment | Tutorial group | Code | Input | Output | Report |
|---|---|---|---|---|---|
| **01 baseline index + QA** (round2, 2026-10-29 14:13–15:11 UTC) | A | `round2/scripts/run_experiment.py` (smoke/full), `safe_api.py`, `retrieval_probe.py`, `budget_sensitivity.py`, `collect_query_evidence.py` | `data/documents/*.txt` (20), `results/questions.json` (Q01–Q10), `round2/evidence/optional_question11.json` | `round2/storage_full/` (612 nodes / 994 edges), `results/full_Q*_{naive,mix}.json`, `supplement_budget_*.json`, `evidence/full_audit_*`, `retrieval_rank_probe.json`, `logs/api_0001–0392` | `LightRAG实验报告/…_zh (1).html` = `round2/report/` |
| **02 source-field ablation + artificial chunking control** (round3, 10-29 16:01–16:25 UTC) | B | `round3/scripts/prepare_ablation.py`, `prepare_chunks.py`, `run_ablation.py`, `run_chunk_control.py`, `parse_chunk_outputs.py`, `official_parser_selective.py` | experiment 01's `logs/api_0392_request.json` (the frozen Q11 context); the text of claims 26–28 of US7991757B2 | `round3/conditions/`, `results/ablation_{A,B,C}_r{1-3}.json`, `chunk_{SAME,CROSS}_r*_c*.json`, `logs/api_*` (21 calls) | `…_zh (2).html` = `round3/report/` (the complete round-two report is appended) |
| **03 chunk boundary, full pipeline** (round4_full_20261030, 10-30 03:27–03:46 UTC; the report calls itself the “third-round Chunk Boundary Ablation complete-pipeline supplementary report”) | C | `round4_full_20261030/scripts/run_pipeline.py`, `custom_chunker.py`, `group_watchdog.py`, `naive_watchdog.py`, `run_naive_followup.py`, `evaluate_F0*.py` | 3 patents (F01 US9589231B2 / F05 US8069128B2 / F04 US8509827B2), `conditions/frozen_groups.json` | `storage/` (18 sets), `results/F0x_*/{chunks,parsed_extraction,merged_graph,natural_query,natural_naive,forced_diagnostic}.json`, `logs/api_*` (364 calls) | `…_zh (4).html` = `round4_full_20261030/report/` |
| **04 merged-node audit** (round2_multisource_audit, 10-30, read only, $0) | D | `round2_multisource_audit/source_mapping_audit.py`, `scripts/*` | experiment 01's **original** `storage_full` (612 nodes) | `dossiers/`, `reviews/`, `evidence/`, item-level conclusions on 38 multi-source nodes | `LightRAG_round2_multisource_node_audit_zh.html` |
| supporting: round1 data + chunk pre-check (10-29, 0 LLM calls) | — | root `scripts/data_*.py`, `chunk_probe.py`, `build_questions.py`, `map_question_chunks.py` | the first 100 rows of Dis2Pat train (revision `eda4a497…`) | `data/`, `results/{questions,chunk_probe,question_chunk_mapping,…}.json` | root `report/…_zh.html` (not in `LightRAG实验报告/`) |
| supporting: round4 pilot (10-30, partly completed) | — | `round4/scripts/*` | trimmed claims 1+27 of US7991757B2 | 9 minimal extractions + 3 forced diagnostics | `round4/report/…_zh.html` (not in the report folder) |
| supporting: environment diagnosis (10-30) | — | `env_diagnostics_20261030/scripts/*` | — | root-cause record of the import stall + smoke index | `env_diagnostics_20261030/report/…environment_diagnostic_zh.html` |

**Which copy holds original and rerun results:**

| Round | Original (matches the report) | 11-05 rerun | Rerun status |
|---|---|---|---|
| round2 | B = C | A | complete: 20 documents processed, 642 nodes / 998 edges (original 612/994), 22 QA calls + supplementary questions, ledger CNY 1.78 |
| round3 | A = C | B | complete: 9 ablation runs + 12 chunk extractions |
| round4_full | A = B | C | complete: 18 indexes + naive follow-up |

At the time of the audit none of the three reruns had **a report or scores** (`START_HERE.txt` says that “new results must be scored again by hand”). A first look: in the rerun, Q11 mix did not repeat the “different patent family” misattribution; Q06 mix gave a comparison this time, but US7991757B2 was still missing from its references. Results vary from run to run. (The reruns were scored later; see [REPRODUCIBILITY.md](REPRODUCIBILITY.md).)

---

## c. Differences and versions

**Between A/B/C**: the shared parts (data, src, round1, round4 pilot, merged-node audit, env_diagnostics) are byte-identical. The only differences: (1) the round each copy reran; (2) `config/repro_session.*`; (3) the start command in `START_HERE.txt`; (4) a few `__pycache__` files.

**Rerun scripts vs original scripts** (`diff`, round2 as the example): only timing, session and configuration paths changed (`repro_runtime.get_runtime()` replaces fixed UTC constants, `CONFIG_PATH` replaces the fixed `<EXTERNAL_DISK>/...`, the ledger gained a session check); **experiment logic, parameters and prompts are unchanged**. The same holds for the round3 and round4_full rerun scripts (the files modified on 11-05 at 04:24 are only safe_api/run_*/watchdog/repro_runtime).

**Differences from upstream LightRAG**: none. See conclusion 3.

**Versions**
| Item | Value | Source |
|---|---|---|
| LightRAG | v1.5.7, API 0344, commit `28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c` (`git ls-remote` confirms = upstream tag v1.5.7, released 2026-09-02) | `evidence/official_release_check.json`, `lightrag/_version.py` |
| Version pitfall | the distribution metadata installed in the round1/2 environment says 1.5.8 (main), but `sys.path` imports the v1.5.7 source first, and the code asserts `__version__=='1.5.7'` | round2 report §A, `env_diagnostics` report §2 |
| Python | original 3.10.6 (round4_full used `<TMP>/lightrag-envdiag-20261030/venv`, based on the system Python 3.10.6); the author's conda environment `lightrag` is 3.10.22 | `evidence/environment_preflight.json`, round4_full report §A |
| Dependencies | NumPy 2.2.6 / PyYAML 6.0.3 / NetworkX 3.4.2 and others, full list | `evidence/requirements_installed.json` |
| LLM | SiliconFlow `deepseek-ai/DeepSeek-V4.1-Flash`, temperature=0, enable_thinking=false, max_tokens=3500, no retries | `round2/evidence/full_settings.json`, `public_runtime_config.json` |
| Embedding | `BAAI/bge-m3`, 1024 dimensions, 8192-token limit | same |
| Storage | JSON KV + NanoVectorDB + NetworkX (defaults) | round2 report §A |
| Key parameters | chunk 1200 / overlap 100 / tokenizer o200k_base; gleaning=0 (source default 1); top_k=12, chunk_top_k=8, entity/relation 2000 each, total 8000 (below the source defaults 40/20/6000/8000/30000); rerank off | `full_settings.json` |

**Upstream state at the time of the audit** (checked 2026-11-12): the newest release was still v1.5.7; `main` was the 1.5.8 development version (HEAD `cec2aaa`). `main`'s `operate.py:5708/5725` still removed `file_path` in the KG context, and the KG context template in `prompt.py` was unchanged → **P1 still existed in the newest code**. Related issues: #4201 (generation continues after rerank/truncation removed all evidence; closed 11-10; a different scenario), #4221 (open PR letting `max_total_tokens` also bound the KG context; related to P2's budget setting), #1323 (open; merging differently spelled entities, the opposite direction of P6), #3346 (citations appearing only sometimes, a user report). No issue was found that discusses the loss of document identity in the KG context. The check was repeated on 2026-11-15 (addition 10).

---

## d. The two HTML tutorials

**“Two routes on a Mac”**: H = an offline copy (read historical results, recompute existing evidence, 0 model calls); N = copies for real new runs (LLM/embedding called again, one separate folder each for A/B/C). The tutorials call the four experiments groups A/B/C/D, which correspond to 01/02/03/04 above. Note: round3's ablation conditions are also called A/B/C (original / source-enhanced / sources + text), and round4_full's chunking conditions A/B (same chunk / cross chunk); the repository had to rename them to avoid confusion.

**What the revision changed** (only section 2 and the paths; the experiment commands and evaluation limits of sections 3–7 are unchanged):
| Original | Revision |
|---|---|
| section 2 “adaptation gates before real API runs”: lists 5 obstacles (old `.env` path, expired UTC deadlines, group C pointing to a defunct `<TMP>` environment, group B's parser needing a clean git checkout, pricing/scoring) and asks the author to edit `safe_api.py` by hand, create `config/repro.env`, `export LIGHTRAG_REPRO_START_UTC` | section 2 “starting on this machine and a fixed run session”: dot has made these adaptations; the first run writes `config/repro_session.json` with a fixed start and reuses it afterwards; the key is read from `<EXTERNAL_DISK>/LightRAG/secrets/.env` by default; B's parser points to `<DOWNLOADS>/LightRAG_PINNED_28ff1b05` |
| uses the variables `$LR_A/$LR_B/$LR_C` | fixed `<ORIG_COPY>/LightRAG_NEW_{A,B,C}` |
| “not yet tested on your Mac” | “wrapper and startup verified offline, no real model called” |

Both tutorials are kept by the author and not published; [SETUP.md](SETUP.md) merges them.

---

## e. Experiment audit: do the conclusions really come from LightRAG?

### e1. Glue-code checklist
| Check | Result | Basis |
|---|---|---|
| document id passed at insertion | ✅ `ids` = publication number | `round2/scripts/run_experiment.py:57`; `round4_full…/run_pipeline.py:70` |
| file_path passed at insertion | ✅ `file_paths` = `<number>.txt` | same |
| identity in the document text | ✅ first line `Publication number: …` | `data/documents/US7991757B2.txt` |
| `source_id`, `file_path` stored on entities/relations | ✅ e.g. Registration Module `file_path=US7991757B2.txt`, `source_id=US7991757B2-chunk-000<SEP>…-001` | `data.entities` in `round2/results/supplement_budget_Q11_supplementary_mix.json` |
| chunk `full_doc_id` | ✅ (the audit groups by `text_chunks.full_doc_id → full_docs`, 0 missing) | merged-node audit report, “how the source statistics are reproduced” |
| citation feature used | ✅ `aquery_llm` + `include_references=True` | `run_experiment.py:76–83` |
| LightRAG source modified | ❌ not modified | see c |
| does the LLM wrapper change LightRAG's behaviour | it only adds: max_tokens cap 3500, temperature 0, thinking off, no retries, 85 s timeout, cost ledger; `response_format` is passed through unchanged (v1.5.7 does not use JSON extraction by default, and the requests contain no `response_format`) | `round2/scripts/safe_api.py:124–150`; `logs/api_0191_request.json` |
| does the problem remain with provenance in use | **yes**. The loss is between “retrieval result → generation prompt”: the entity/relation JSON the model sees contains only `entity/type/description` and `entity1/entity2/description` | `round2/logs/api_0392_request.json`; `operate.py:5462–5494, 5761–5766, 5813–5829` |

### e2. Problems and attribution

Attribution categories: **design** = a design trade-off of LightRAG; **implementation** = an implementation problem of LightRAG; **config/env**; **experiment code**; **model generation** (fifth category, added at the author's decision in phase two: the model fabricates although the evidence is complete). This audit **found nothing attributable to “implementation”**.

| ID | Phenomenon (one sentence) | Layer where it is lost | Main attribution | Secondary factors | Evidence |
|---|---|---|---|---|---|
| P1 | graph facts were retrieved and carry sources in storage, but the answer says they “belong to a different patent family” and cites US10867122B1 (Q11 mix, extended budget) | document identity: lost when the KG context is serialised | **design** (the KG context carries no `file_path`/`source_id`; the reference list comes only from chunks) | experiment code: user_prompt requires “a publication number only when it appears in the evidence”; generation behaviour | round2 report §C failure case; `round2/logs/api_0392_request.json`; `supplement_budget_Q11_supplementary_mix.json`; round3 report §2 (with source fields added, 3/3 identify the patent) |
| P1′ | adding source fields back identifies the patent but the claim number still cannot be answered; only the claim text makes the answer right | evidence provenance: `source_id` is an aggregated chunk-level source, with no claim or character span | **design** (citation granularity at document/chunk) | — | round3 report §2, §4 |
| P2 | at the baseline budget the Q06 cross-document comparison lacks one patent's text; recovered with a larger budget | retrieval: the target chunks rank 9 and 11, below top-8 | **config** (budget below the source defaults) | design: purely semantic retrieval; the publication number in the query is not matched exactly | round2 report §B sensitivity check; `round2/evidence/retrieval_rank_probe.json` |
| P3 | Q11 does not retrieve the US7991757B2 text even at top-20 (ranks 29, 30) | retrieval | **design** (no filtering by publication number, no lexical recall) | config: budget | same |
| P4 | one relation of US9218390B2 cut off because the output reached the 3500-token cap; the edge is missing from the graph | technical relations: extraction | **config** (dot set max_tokens=3500) | LightRAG logs the truncation and drops the incomplete line, as expected | round2 report §C; `round2/logs/api_0191_response.json` (`finish_reason=length`); 2 more truncations in round4_full |
| P5 | with an artificial mid-sentence split (93 tokens) the complete relation is kept 0/3 times, same chunk 3/3 | technical relations: independent per-chunk extraction | **design** (each chunk is extracted on its own, no joint cross-chunk extraction) | config: gleaning=0; a tiny, artificially built stress test | round3 report §3 |
| P5′ | with the full document, F01's cross-chunk condition keeps the predicate 0/3 times, same chunk 3/3; but the target sentence is **complete** in B's chunk, and there is only 1 clean pair | technical relations: unstable extraction representation | **to be verified** (looks more like the LLM extraction's sensitivity to context than a cut) | config: 2 truncations | round4_full report §C, §D |
| P6 | 38 of 612 nodes are same-name merges from ≥2 patents; 6 of them juxtapose homonyms or roles (e.g. Token means both “anonymisation substitute” and “query token”) | document identity: node-level merge, sources joined with `<SEP>` | **design** (entities merged by name) | no resulting wrong edge or propagation into answers observed | merged-node audit report |
| P7 | claim dependencies (e.g. 11→10→9→1) are not built into the graph; citations stop at the document | technical relations + evidence provenance | **design** (default entity types contain no claims; citation granularity at document level) | — | round2 report §D; round4_full report §E |
| P8 | with complete evidence, naive still invents a claim-dependency chain (F01_B_r2); Q01 mix infers “the only one in the set”; quoted text not strictly verbatim | generation | **model generation** (fifth category, see addition 3; model deepseek-ai/DeepSeek-V4.1-Flash) | — | round4_full report §D; round2 report §B |
| P9 | ablation condition C maps `[1]` to US7991757B2 in all three runs, conflicting with the frozen reference list | citation numbers | **experiment code** (the reference list was not updated, to keep the ablation pure) | — | round3 report §2, §4 |
| P10 | round3/4 run the official parser not through a normal import but by selectively executing the original functions via AST | — | **config/env** (dependency files in the dataless state made imports hang; root cause undetermined) | experiment code: the substitute path was checked for equivalence only on the saved API 191 groups | round3 report §5; env_diagnostics report §1 |
| P11 | the first resumed run of round4_full exited before any API call because the wrapper lacked `mkdir(parents=True)` | — | **experiment code** (fixed, no effect on results) | — | round4_full report §A, last paragraph; `run_pipeline_pre_setup_fix.py` |
| P12 | distribution metadata 1.5.8, but the 1.5.7 source actually ran | — | **config/env** | guarded by path and assertion | round2 report §A |

### e3. Open points (not stated explicitly in the reports, to be made clear in the README)
1. **The name of round4_full**: the folder is called round4, the report title says “third round”. The repository names experiments by content and gives a mapping.
2. **P1's misattribution occurred only once**: round3 replayed the same context 3 times (condition A) without repeating it, nor did the 11-05 rerun. → The README can only say “observed once”, not describe a stable phenomenon.
3. **Every run is a single run** (round3 and round4_full with 3 repeats each, temperature=0, no seed), 20 patents, not randomly sampled; the scoring is AI-assisted item-by-item checking, not independent human annotation (as the reports themselves say).
4. **The 11-05 rerun is a ready-made second independent run**, but it was not scored at the time. It is the most weighty material for “limitations and open points”. (Scored later; see [REPRODUCIBILITY.md](REPRODUCIBILITY.md).)
5. **dot's user_prompt is itself a confounder** (P1): it asks for a publication number only when the number appears in the evidence, and the KG context contains no numbers. Whether the model would still misattribute with LightRAG's default prompt (no user_prompt) is **not known**.

---

## f. Proposed layout (draft at the time, for the author's confirmation)

```
lightrag-patent-provenance/
  README.md / README_en.md / demo script
  requirements.txt            # lightrag-hku==1.5.7 + the pinned versions of evidence/requirements_installed.json
  .python-version             # 3.10
  .env.example / .gitignore / THIRD_PARTY_NOTICES.md (LightRAG MIT notice)
  data/                       # the 20 documents + claims + manifests + PROVENANCE.md (Dis2Pat revision, Google Patents check)
  experiments/
    00_data_and_chunk_probe/  # round1 (supporting, optional)
    01_baseline_index_qa/     # round2
    02_provenance_ablation_and_chunk_control/   # round3
    03_chunk_boundary_full_pipeline/            # round4_full_20261030
    04_merged_node_audit/     # round2_multisource_audit
      README.md  run.sh  config/  scripts/  results/ (key output of the original run)
      results_rerun_20261105/ (the author's rerun, marked “not scored”)
  supporting/                 # reports and some key evidence of the round4 pilot and env_diagnostics
  reports/original/           # the 7 original HTML files unchanged + a .md each
  docs/SETUP.md  docs/AUDIT.md  docs/archive/ (the two old tutorials)
  figures/
  runs/                       # .gitignore: complete LightRAG working directories, all API logs, tiktoken_cache
```

| Treatment | Content |
|---|---|
| keep in git | all of dot's experiment scripts (one copy each); results/evidence/conditions of the original run; reports; data documents/claims/manifests; the individual API logs the README cites (e.g. api_0191, api_0392) |
| deduplicate | 3 copies → 1; 6 LightRAG source copies + 3 source archives → pip `lightrag-hku==1.5.7` (`.py` files checked byte-identical, no patch needed) |
| local only (`runs/`) | `storage*/` (31M), all `logs/api_*` (~57M), `tiktoken_cache`, raw env_diagnostics logs (5000+ `<TMP>/...` paths), `config/repro_session.*` |
| not copied | `.DS_Store`, `__pycache__`, dot's packaging metadata (MANIFEST/checksums contain absolute paths and old hashes and would be invalid once copied) |
| left to the author | whether the first 100 raw Dis2Pat rows (6.4M) and the 20 Google Patents HTML pages (8M) go into git |

The final layout is described in the [README](../README.md#layout).

---

## Scan for keys and absolute paths (read only)
- **No real API key found.** The only match is `myapikey` in the upstream example file `lightrag/api/.env.aoi.example` (removed together with the deduplicated source). The key was always kept in `<EXTERNAL_DISK>/LightRAG/secrets/.env` and never entered the package.
- Absolute paths are frequent: `<HOME>/Documents/Codex/...` (7610 occurrences, mainly in logs/status files of dot's original working directory), `<TMP>/lightrag-envdiag-*` (~6800, mainly env_diagnostics logs), `<ORIG_COPY>/LightRAG_NEW_*` (~200), `<EXTERNAL_DISK>/...` (46).
- The 4 formal reports are almost clean: only `(4).html` contains 1 `<TMP>/...venv/bin/python`. The two tutorials contain 2 and 10 `<HOME>/...` paths and 1 `<EXTERNAL_DISK>/...`.

---

## Expected time and cost (from the reports; estimates, not invoices)
| Experiment | Model calls | Wall clock | Cost |
|---|---|---|---|
| 01 | 95 LLM + 297 embedding | about 31 minutes of API time (the 20-document baseline run about 15 minutes) | CNY 1.56–1.77 |
| 02 | 21 LLM | about 25 minutes (including preparation) | CNY 0.15–0.65 |
| 03 | 117 LLM + 247 embedding | about 19 minutes | CNY 1.08–1.33 |
| 04 | 0 | offline | CNY 0 |

LLM cache replay: experiment 01's `kv_store_llm_response_cache.json` has 26 query and 11 keyword entries, so a rerun of the queries with the same parameters could in principle hit the cache without calling the LLM; the query vectors would still need bge-m3 (listed as free in the reports, but needing a key and network). The truncated extraction of API 191 is not cached; rebuilding the index would call it again. A later phase could verify with an LLM function that raises whether a replay really makes 0 LLM calls (done; see [SETUP §7](SETUP.md#7-can-the-llm-cache-make-reruns-fast-and-consistent)).

---

## Additions in phase two (2026-11-13)

### Addition 1: where report (3) went
`LightRAG实验报告/` contains only (1), (2), (4) and node_audit, because the numbers are suffixes the browser added to repeated downloads. `<DOWNLOADS>/LightRAG_patent_provenance_report_zh (3).html` (downloaded 10-30) is **byte-identical** to (2) (SHA256 prefix `a0ac0bade480`), i.e. the round-three report was downloaded twice. The one without a number equals (1). Where each file of the report folder went: [reports/README.md](../reports/README.md).

### Addition 2: comparison of the same-name folders in Downloads
See [NAMING.md §5](NAMING.md#5-same-name-folders-in-downloads-compared-2026-11-12). In short:
- `LightRAG_NEW_A/B/C` are identical file by file to those in `lightRAG_exp`;
- `reproduction_bundle_20261104/lightrag_patent_20261029` and `LightRAG_OFFLINE_WORK_20261104` both hold dot's original results;
- `LightRAG_OFFLINE` is the copy in which the author rebuilt the reports offline on 11-05; the rebuilt reports differ from the originals only in timestamps;
- `LightRAG_PINNED_28ff1b05` is a clean upstream checkout.

### Addition 3: the fifth attribution category, “model generation”
P8 moved to this category: the evidence was completely in the context, and the model still wrote something that contradicts the original (F01_B_r2 naive's claim-dependency chain; Q01 mix's inference “the only one in the set”; quotes not verbatim). Model: SiliconFlow `deepseek-ai/DeepSeek-V4.1-Flash`, temperature=0, enable_thinking=false. No other model was tried for comparison, so it **cannot** be said that this is specific to this model, nor that another model would remove it.

### Addition 4: why experiment 02's parser needs a clone
It reads `.py` source text and adds a git verification; it **reads no non-`.py` file** and does not rely on `sys.path` imports:
- `official_parser_selective.py` reads 4 files with `path.read_text()` (`lightrag/_version.py`, `constants.py`, `utils.py`, `operate.py`) and executes their unmodified parser functions selectively via AST. A normal `import` was avoided because imports hung in the environment at the time (see [SETUP §1.1](SETUP.md#11-imports-that-stall-for-minutes)).
- `parser_source.verify_source()` additionally verifies with git: `rev-parse HEAD == 28ff1b05`, origin is the official repository, clean work tree, each file byte-identical to `git show 28ff1b05:<file>`.
- The SHA256 of these 4 files in the pip package `lightrag-hku==1.5.7` equals the pinned checkout (checked).

Avoiding the clone would be technically possible, but only by replacing the git verification in `verify_source()` with a SHA256 check of the pip files, i.e. by changing experiment code. **Decision (2026-11-13): keep dot's git verification; the code is not changed.** Only the path changed: the checkout defaults to `runs/LightRAG_PINNED_28ff1b05`; clone commands in [SETUP §6.1](SETUP.md#61-pinned-checkout-for-experiment-02s-parse-step). It is needed only when a paid rerun of experiment 02 reaches the `parse` step; offline replay and the other experiments do not need it. Verified with an existing checkout on the author's machine: the verification passes in the new layout.

### Addition 5: Dis2Pat licence
The Hugging Face dataset card states **CC-BY-SA-4.0** (checked through the API on 2026-11-12; revision `eda4a497…` equals the one at fetch time), which permits redistribution. The repository contains only the 20 records actually used and files derived from them, with attribution. See [data/README.md](../data/README.md).

### Addition 6: date and commit of the upstream check (2026-11-12)
- The newest upstream tag was still `v1.5.7` (= `28ff1b05f2ac3f3e6fa14dd2cd33656579bd0c9c`); `main`'s HEAD was `cec2aaa2f09349f8d06ec39797f371da97883831`, `_version.py` 1.5.8 / API 0348.
- Lines 5708 and 5725 of `main`'s `lightrag/operate.py` still removed `file_path` before the KG context was assembled (lines 5467 and 5484 in v1.5.7). Superseded by addition 10.

### Addition 7: live reproduction on the existing index (no LLM call)
`tools/demo_context_provenance.py` runs LightRAG's own `mix` pipeline on a copy of experiment 01's original index, with the LLM forbidden. Its output is deterministic. Since 2026-11-15 it uses the saved bge-m3 vectors of the original Q11 query (earlier: a stand-in vector) and reproduces the original Q11 retrieval exactly: all 82 entities and 82 relations carry `file_path` in the structured result, and none of them in the context sent to the model. See [context_provenance_demo.md](../experiments/01_baseline_index_qa/results/key_evidence/context_provenance_demo.md).

### Addition 8: qualitative check of the second run (2026-11-05)
See [RERUN_20261105_CHECK.md](RERUN_20261105_CHECK.md).
- The structural phenomenon reappeared: in the rerun's prompt for the same question, `file_path` and `source_id` occur 0 times.
- The 3500-token truncation reappeared (4 times).
- The artificial mid-sentence split gives SAME 3/3, CROSS 0/3, as in the original.
- The citation-number conflict of ablation condition C reappeared 3/3.
- The Q11 “different patent family” misattribution did **not** reappear.
- F01's same-chunk/cross-chunk difference was **not** cleanly reproduced (cross-chunk r3 kept the predicate).

### Addition 9: non-path changes made to dot's scripts during curation
Only one kind: the fixed personal research-interest paragraph in 4 report-generation scripts was replaced by placeholder text, and the corresponding word-count assertions were removed. See `CONTENT_CHANGES.diff` in each experiment folder. This only affects the text of that section of the reports, not any experiment computation.

---

## Additions in phase three (2026-11-15): full reruns and reproducibility

- **Why the sources are removed**: upstream commit [`d3fde609`](https://github.com/HKUDS/LightRAG/commit/d3fde60938c7e14f5e5dff07d4fbd4196e86cbce) (2025-08-18), “refactor: remove file_path and created_at from context, improve token truncation”. Before this commit the context carried `file_path` (with `<SEP>` replaced by `;`). “Intentional” is therefore documented and the attribution “design trade-off” stands; the commit does not state a reason, and “to save tokens” is an inference.
- **Full rerun**: experiments 01–03 were rerun with this repository's `run.sh live`, same model and parameters; ledger estimate about CNY 3.75. Before that, two run directories failed before any API call (`runs/aborted_no_api_*`) and were fixed: one lacked an output directory, the other a script-path mapping.
- **Scoring**: 13 judgments were defined ([`SCORING_RUBRIC.md`](SCORING_RUBRIC.md)); on the original run they agree with dot's original labels 242/242. The three-run comparison is in [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md).
- **Effect on the attributions**: P1, P6 and P7 reproduced in all three runs; attributions unchanged. P5′ disagrees across the three runs (cross-chunk kept 0/3, 1/3, 3/3) and stays “to be verified”. The Q11 misattribution and P8 each occurred only once.

### Addition 10: upstream checked again (2026-11-15)
- The newest GitHub release is `v1.5.8rc1` (a release candidate published on 2026-11-15; `_version.py` 1.5.8 / API 0350); the newest version on PyPI is still 1.5.7.
- `main`'s HEAD is [`c9ef958b3af62e5bb155cee395089a341342bfac`](https://github.com/HKUDS/LightRAG/commit/c9ef958b3af62e5bb155cee395089a341342bfac) (`_version.py` 1.5.8 / API 0351). Its `lightrag/operate.py` is identical to the one of `v1.5.8rc1`.
- Both still remove `file_path` and `created_at` before the KG context is written ([main L5765–L5797](https://github.com/HKUDS/LightRAG/blob/c9ef958b3af62e5bb155cee395089a341342bfac/lightrag/operate.py#L5765-L5797); the context lines are written from the stripped records at [L6089–L6094](https://github.com/HKUDS/LightRAG/blob/c9ef958b3af62e5bb155cee395089a341342bfac/lightrag/operate.py#L6089-L6094)). P1 still applies to the newest code.
