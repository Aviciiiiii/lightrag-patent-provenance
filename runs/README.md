# runs/ (local only)

Everything in this directory except this README is git-ignored (about 220 MB on the author's machine).
Rebuild it from dot's evidence package with:

    python tools/setup_local_runs.py --a <path>/LightRAG_NEW_A --b <path>/LightRAG_NEW_B --c <path>/LightRAG_NEW_C

| path | content |
|---|---|
| `01_baseline_index_qa/original/` | original LightRAG working dirs (`storage_full`, `storage_smoke`), all API logs, original report folder. `storage_full/patent_r2_full` is also committed in `experiments/01_baseline_index_qa/index/`, and the committed copy is used first |
| `01_baseline_index_qa/rerun_20261105/` | the 2026-11-05 second run (run by the author on their own machine): working dirs + API logs |
| `02_provenance_ablation_and_chunk_control/{original,rerun_20261105}/` | API logs (+ report folder) |
| `03_chunk_boundary_full_pipeline/{original,rerun_20261105}/` | the 18 working dirs + API logs |
| `tiktoken_cache/` | o200k_base tokenizer cache (otherwise downloaded by tiktoken) |
| `round1_report/` | round1 report folder (CSS source for dot's report builders) |
| `archive/` | round4 pilot, environment diagnostics, Google Patents pages, raw Dis2Pat rows, dot's original scripts and LightRAG source archives |
| `offline_<exp>_<UTC>/` | scratch copies created by `experiments/*/run.sh offline` |
| `rerun_<exp>_<UTC>/` | fresh live reruns created by `experiments/*/run.sh live new` |
| `demo_context/` | index copy used by `tools/demo_context_provenance.py` |
| `LightRAG_PINNED_28ff1b05/` | (optional) upstream checkout for experiment 02's parser step |
