#!/usr/bin/env bash
# Experiment 01 — baseline index & QA (dot's round2). See README.md in this folder.
set -euo pipefail
NAME=01_baseline_index_qa
LEGACY=round2
OFFLINE_COPY=(results evidence runs:logs runs:storage_full runs:storage_smoke)
OFFLINE_STEPS=("scripts/collect_query_evidence.py" "scripts/build_report.py")
OFFLINE_COMPARE=(results evidence)
SEED=(evidence/optional_question11.json)
FREE_STEPS=""
LIVE_STEPS=("preflight=scripts/safe_api.py" "smoke=scripts/run_experiment.py smoke" "full=scripts/run_experiment.py full"
            "probe=scripts/retrieval_probe.py" "budget=scripts/budget_sensitivity.py")
COST_NOTE="Original full run: 95 LLM + 297 embedding calls, ~31 min of API time, estimated CNY 1.56-1.77 (not an invoice); in-script hard cap CNY 10."
source "$(cd "$(dirname "$0")/../.." && pwd)/tools/run_common.sh"
main "$@"
