#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/env.sh"
vdot_workload=${1:-vdot_smoke}
case "$vdot_workload" in
  vadd_test) vdot_marker=VADD_PASS ;;
  vdot_smoke|vdot_test) vdot_marker=VDOT_PASS ;;
  benchmark) vdot_marker=BENCH_PASS ;;
  *) printf 'Unknown validation workload: %s\n' "$vdot_workload" >&2; exit 2 ;;
esac
vdot_emu="$NOOP_HOME/build/emu"
vdot_reference=${VDOT_REF_SO:-$VDOT_ROOT/build/nemu/reference/riscv64-nemu-interpreter-so}
test -x "$vdot_emu" || { printf 'Build emu first.\n' >&2; exit 2; }
test -f "$vdot_reference"
vdot_run_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
vdot_report="$VDOT_ROOT/reports/rtl-$vdot_workload-$vdot_run_id"
mkdir -p "$vdot_report"
vdot_command=("$vdot_emu" -i "$VDOT_ROOT/build/workloads/$vdot_workload.bin" \
  -F "$VDOT_ROOT/build/workloads/flash.bin" --ram-size=128MB \
  "--diff=$vdot_reference" -C "${VDOT_MAX_CYCLES:-5000000}")
if [[ -n "${VDOT_WAVE_BEGIN:-}" || -n "${VDOT_WAVE_END:-}" ]]; then
  [[ "${VDOT_WAVE_BEGIN:-}" =~ ^[0-9]+$ && "${VDOT_WAVE_END:-}" =~ ^[0-9]+$ ]] || exit 2
  vdot_command+=(--dump-wave-full -b "$VDOT_WAVE_BEGIN" -e "$VDOT_WAVE_END" \
    "--wave-path=$vdot_report/wave.fst")
fi
printf '%q ' "${vdot_command[@]}" > "$vdot_report/command.txt"
printf '\n' >> "$vdot_report/command.txt"
python3 "$VDOT_ROOT/scripts/source_manifest.py" "$vdot_report/source.json"
sha256sum "$vdot_emu" "$vdot_reference" "$VDOT_ROOT/build/workloads/$vdot_workload.bin" \
  "$VDOT_ROOT/build/workloads/flash.bin" > "$vdot_report/artifacts.sha256"
printf 'RTL evidence: %s\n' "$vdot_report"
if systemd-run --user --scope --unit="vdot-rtl-$vdot_run_id" \
  -p MemoryMax=3G -p MemorySwapMax=0 /usr/bin/time -v -o "$vdot_report/time.txt" \
  "${vdot_command[@]}" > "$vdot_report/run.log" 2>&1; then
  vdot_status=0
else
  vdot_status=$?
fi
printf '%s\n' "$vdot_status" > "$vdot_report/exit-status.txt"
test "$vdot_status" == 0
python3 "$VDOT_ROOT/scripts/check_run.py" "$vdot_report/run.log" "$vdot_marker"
