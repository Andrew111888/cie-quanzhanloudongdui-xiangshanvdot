#!/usr/bin/env bash
# Continue local validation after a particular persistent model build succeeds.
set -euo pipefail
source "$(dirname -- "$0")/env.sh"

if [[ "${1:-}" != --worker ]]; then
  [[ $# == 2 ]] || { printf 'Usage: %s model-build-report fault-reference.so\n' "$0" >&2; exit 2; }
  vdot_build_report=$(realpath "$1")
  vdot_fault_ref=$(realpath "$2")
  test -s "$vdot_build_report/unit.txt" && test -f "$vdot_fault_ref"
  vdot_run_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
  vdot_report="$VDOT_ROOT/reports/rtl-queue-$vdot_run_id"
  vdot_unit="vdot-validate-$vdot_run_id"
  mkdir -p "$vdot_report"
  printf '%s\n' "$vdot_unit.service" > "$vdot_report/unit.txt"
  systemd-run --user --unit="$vdot_unit" --working-directory="$VDOT_ROOT" \
    -p MemoryMax=3G -p MemorySwapMax=0 \
    -p "StandardOutput=append:$vdot_report/service.log" -p StandardError=inherit \
    /bin/bash "$VDOT_ROOT/scripts/validate_rtl_when_ready.sh" --worker \
    "$vdot_build_report" "$vdot_fault_ref" "$vdot_report"
  printf 'VALIDATION_QUEUED unit=%s.service report=%s\n' "$vdot_unit" "$vdot_report"
  exit 0
fi

[[ $# == 4 ]] || exit 2
vdot_build_report=$2 vdot_fault_ref=$3 vdot_report=$4
exec >> "$vdot_report/queue.log" 2>&1
trap 'vdot_exit=$?; printf "%s\n" "$vdot_exit" > "$vdot_report/exit-status.txt"' EXIT
vdot_build_unit=$(cat "$vdot_build_report/unit.txt")
printf 'waiting for %s\n' "$vdot_build_unit" > "$vdot_report/current-step.txt"
while [[ ! -s "$vdot_build_report/exit-status.txt" ]]; do
  if ! systemctl --user is-active --quiet "$vdot_build_unit"; then
    printf 'Model build ended without a completion record.\n' >&2
    exit 1
  fi
  sleep 15
done
[[ $(cat "$vdot_build_report/exit-status.txt") == 0 ]]
while [[ ! -s "$vdot_build_report/emu.sha256" ]]; do
  if ! systemctl --user is-active --quiet "$vdot_build_unit"; then
    printf 'Model build has no artifact checksum.\n' >&2
    exit 1
  fi
  sleep 1
done
(cd "$NOOP_HOME" && sha256sum --check "$vdot_build_report/emu.sha256")

run_step() {
  local vdot_step=$1
  shift
  printf '%s\n' "$vdot_step" > "$vdot_report/current-step.txt"
  printf 'START %s\n' "$vdot_step"
  "$@" > "$vdot_report/$vdot_step.log" 2>&1
  printf 'PASS %s\n' "$vdot_step"
}

run_step emu-help "$NOOP_HOME/build/emu" --help
run_step vadd bash "$VDOT_ROOT/scripts/run_rtl.sh" vadd_test
run_step vdot-smoke bash "$VDOT_ROOT/scripts/run_rtl.sh" vdot_smoke
run_step fault-check bash "$VDOT_ROOT/scripts/run_fault_check.sh" "$vdot_fault_ref"
run_step vdot-random bash "$VDOT_ROOT/scripts/run_rtl.sh" vdot_test
run_step latency-probe bash "$VDOT_ROOT/scripts/run_rtl.sh" latency_probe
run_step benchmark bash "$VDOT_ROOT/scripts/run_rtl.sh" benchmark
python3 - "$vdot_report" <<'PY'
from pathlib import Path
import re
import subprocess
import sys
report = Path(sys.argv[1])
driver = (report / 'benchmark.log').read_text()
match = re.search(r'^RTL evidence: (.+)$', driver, re.M)
if not match:
    raise SystemExit('Missing benchmark run directory')
subprocess.run([sys.executable, 'scripts/performance_report.py',
                str(Path(match.group(1)) / 'run.log'), '--engine', 'rtl',
                '--output', str(report / 'performance.md')], check=True)
PY
# This initial window may need refinement after inspecting the actual waveform.
run_step vadd-wave env VDOT_WAVE_BEGIN=0 VDOT_WAVE_END=50000 \
  bash "$VDOT_ROOT/scripts/run_rtl.sh" vadd_test
printf 'RUNS_COMPLETE_WAVE_ANALYSIS_AND_CLEAN_REPRO_STILL_REQUIRED\n' > "$vdot_report/current-step.txt"
printf 'Local validation runs complete; no competition materials were submitted.\n'
