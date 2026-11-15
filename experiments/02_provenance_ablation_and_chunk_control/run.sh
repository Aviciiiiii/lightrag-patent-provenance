#!/usr/bin/env bash
# Experiment 02 — source-field ablation + artificial chunk-boundary control (dot's round3). See README.md.
set -euo pipefail
NAME=02_provenance_ablation_and_chunk_control
LEGACY=round3
OFFLINE_COPY=(conditions evidence results)
OFFLINE_STEPS=("scripts/evaluate_ablation.py" "scripts/evaluate_chunks.py" "scripts/build_report.py")
OFFLINE_COMPARE=(evidence results)
SEED=()
FREE_STEPS="prepare-ablation prepare-chunks parse"
LIVE_STEPS=("prepare-ablation=scripts/prepare_ablation.py" "prepare-chunks=scripts/prepare_chunks.py"
            "ablation=scripts/run_ablation.py" "chunks=scripts/run_chunk_control.py" "parse=scripts/parse_chunk_outputs.py")
COST_NOTE="Original run: 21 LLM calls, 0 embedding calls, estimated CNY 0.15-0.65 (not an invoice); in-script hard cap CNY 10. prepare-* and parse make no API calls."
source "$(cd "$(dirname "$0")/../.." && pwd)/tools/run_common.sh"
main "$@"
