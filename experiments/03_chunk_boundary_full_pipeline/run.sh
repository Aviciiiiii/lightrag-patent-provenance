#!/usr/bin/env bash
# Experiment 03 — chunk-boundary ablation through the full pipeline (dot's round4_full_20261030). See README.md.
set -euo pipefail
NAME=03_chunk_boundary_full_pipeline
LEGACY=round4_full_20261030
OFFLINE_COPY=(conditions evidence results runs:logs runs:storage)
OFFLINE_STEPS=("scripts/audit_completed_runs.py" "scripts/build_final_report.py")
OFFLINE_COMPARE=(evidence results)
SEED=(conditions)
FREE_STEPS=""
LIVE_STEPS=("F01=scripts/group_watchdog.py F01" "F05=scripts/group_watchdog.py F05" "F04=scripts/group_watchdog.py F04"
            "naive=scripts/naive_watchdog.py")
COST_NOTE="Original run: 117 LLM + 247 embedding calls, ~19 min, estimated CNY 1.08-1.33 (not an invoice); in-script hard cap CNY 4. Run F01, F05, F04, then naive."
source "$(cd "$(dirname "$0")/../.." && pwd)/tools/run_common.sh"
main "$@"
