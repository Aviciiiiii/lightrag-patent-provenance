#!/usr/bin/env bash
# Experiment 04 — merged-node audit of experiment 01's original graph (read-only, no API). See README.md.
set -euo pipefail
NAME=04_merged_node_audit
LEGACY=round2_multisource_audit
OFFLINE_COPY=(dossiers evidence reviews report scripts source_mapping_audit.py MANIFEST.json SHA256SUMS.txt package_validation.json)
OFFLINE_STEPS=("scripts/build_inventory.py" "scripts/validate_reviews.py --require-complete" "source_mapping_audit.py"
               "scripts/check_original_documents.py" "scripts/build_report.py")
OFFLINE_COMPARE=(dossiers evidence report)
SEED=()
FREE_STEPS=""
LIVE_STEPS=()
COST_NOTE=""
source "$(cd "$(dirname "$0")/../.." && pwd)/tools/run_common.sh"
main "$@"
