# Shared helpers for experiments/*/run.sh (bash 3.2 compatible). Sourced, not executed.
# Each run.sh sets: NAME (new name), LEGACY (dot's folder name), OFFLINE_STEPS (array of
# "script args" strings), LIVE_STEPS (name=script args), SEED (paths copied into a fresh live run dir),
# COST_NOTE (text shown before any paid step).

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXP="$REPO/experiments/$NAME"
PY="${PYTHON:-python}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
CURRENT="$REPO/runs/$NAME.current_rerun"

die() { echo "ERROR: $*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: experiments/$NAME/run.sh <command>

  check            no-LLM smoke test: imports, paths, config (never calls an API)
  import <run-dir> [--label YYYYMMDD] [--operator TEXT]
                   copy a finished rerun (results/evidence/conditions + RUN_RECORD.md) into
                   experiments/$NAME/results_rerun_<label>/, sanitized; logs stay in runs/
  offline          replay dot's offline scripts on a scratch copy of the saved results
                   (no API calls; needs the local-only files in runs/, see runs/README.md)
EOF
  if [ ${#LIVE_STEPS[@]} -gt 0 ]; then
    cat <<EOF
  live new         create a fresh run directory runs/rerun_${NAME}_<UTC>/ for a real rerun
  live <step>      run one paid step in the current rerun directory. Steps, in order:
EOF
    for s in "${LIVE_STEPS[@]}"; do echo "                     ${s%%=*}  ->  python ${s#*=}"; done
    cat <<EOF
                   Paid steps refuse to run unless LRP_CONFIRM_COSTS=yes is set.
                   $COST_NOTE
EOF
  fi
}

copy_into() {  # copy_into <dest> <path relative to experiment or 'runs:' path>...
  local dest="$1"; shift
  local p
  for p in "$@"; do
    case "$p" in
      runs:*) local src="$REPO/runs/$NAME/original/${p#runs:}" ;;
      *)      local src="$EXP/$p" ;;
    esac
    [ -e "$src" ] || die "missing $src (local-only files: see runs/README.md)"
    mkdir -p "$dest/$(dirname "${p#runs:}")"
    cp -R "$src" "$dest/${p#runs:}"
  done
}

run_py() {  # run_py <run-dir> "<path relative to experiment> [args...]"
  local work="$1"; local line="$2"
  # shellcheck disable=SC2086
  set -- $line
  local script="$1"; shift
  (cd "$REPO" && LRP_RUN_FOR="$LEGACY" LRP_RUN_DIR="$work" "$PY" "$EXP/$script" "$@")
}

cmd_check() { "$PY" "$REPO/tools/smoke_check.py" "$NAME"; }

cmd_offline() {
  local work="$REPO/runs/offline_${NAME}_$STAMP"
  mkdir -p "$work"
  copy_into "$work" "${OFFLINE_COPY[@]}"
  mkdir -p "$work/report"  # report builders write here (dot kept report/ next to results/)
  echo "scratch copy: runs/$(basename "$work")"
  local step
  for step in "${OFFLINE_STEPS[@]}"; do
    echo "== python $step"
    run_py "$work" "$step" || die "offline step failed: $step"
  done
  echo
  echo "== files that differ from the committed originals (expected: timestamps / regenerated summaries only)"
  local d
  for d in "${OFFLINE_COMPARE[@]}"; do
    diff -rq "$EXP/$d" "$work/$d" | sed "s#$REPO/##g" || true
  done
  echo "done: runs/$(basename "$work")"
}

cmd_live() {
  local step="${1:-}"
  [ -n "$step" ] || die "live needs 'new' or a step name"
  if [ "$step" = new ]; then
    local work="$REPO/runs/rerun_${NAME}_$STAMP"
    # dot's package always had these folders; its scripts write into them without creating them
    mkdir -p "$work/results" "$work/logs" "$work/evidence" "$work/report"
    [ ${#SEED[@]} -eq 0 ] || copy_into "$work" "${SEED[@]}"
    echo "$work" > "$CURRENT"
    echo "new rerun directory: runs/$(basename "$work")"
    echo "outputs of every live step go there; committed results are never touched."
    return
  fi
  [ -f "$CURRENT" ] || die "no current rerun directory; run: experiments/$NAME/run.sh live new"
  local work; work="$(cat "$CURRENT")"
  local entry="" s
  for s in "${LIVE_STEPS[@]}"; do if [ "${s%%=*}" = "$step" ]; then entry="${s#*=}"; fi; done
  [ -n "$entry" ] || die "unknown step '$step'"
  case " $FREE_STEPS " in
    *" $step "*) ;;
    *) [ "${LRP_CONFIRM_COSTS:-}" = yes ] || die "step '$step' calls the paid API. $COST_NOTE Re-run with LRP_CONFIRM_COSTS=yes to proceed."
       [ -f "${LRP_ENV_FILE:-$REPO/.env}" ] || die "missing ${LRP_ENV_FILE:-.env} (copy .env.example, or point LRP_ENV_FILE at your key file)" ;;
  esac
  echo "== [$(basename "$work")] python $entry"
  run_py "$work" "$entry"
}

main() {
  local c="${1:-help}"; shift || true
  case "$c" in
    check) cmd_check ;;
    import) [ ${#LIVE_STEPS[@]} -gt 0 ] || die "experiment $NAME has no reruns to import"; "$PY" "$REPO/tools/import_rerun.py" "$NAME" "$@" ;;
    offline) cmd_offline ;;
    live) [ ${#LIVE_STEPS[@]} -gt 0 ] || die "experiment $NAME has no live steps (offline audit only)"; cmd_live "$@" ;;
    *) usage ;;
  esac
}
