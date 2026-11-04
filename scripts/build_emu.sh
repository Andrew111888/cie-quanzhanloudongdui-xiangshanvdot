#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/env.sh"

vdot_config=${VDOT_CONFIG:-MinimalConfig}
vdot_heap=${VDOT_JAVA_HEAP:-4500m}
vdot_limit=${VDOT_BUILD_MEMORY_MAX:-5500M}
vdot_run_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
vdot_unit=vdot-build-$vdot_run_id
vdot_report="$VDOT_ROOT/reports/$vdot_unit"
mkdir -p "$vdot_report"
export PATH="$VDOT_ROOT/scripts/lowmem-bin:$PATH"
export JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2 -XX:+UseSerialGC'
if [[ -n "${VDOT_HEAP_BACKING_DIR:-}" ]]; then
  mkdir -p "$VDOT_HEAP_BACKING_DIR"
  export JAVA_TOOL_OPTIONS="$JAVA_TOOL_OPTIONS -XX:AllocateHeapAt=\"$VDOT_HEAP_BACKING_DIR\""
fi

python3 "$VDOT_ROOT/scripts/source_manifest.py" "$vdot_report/source.json"
free -b > "$vdot_report/memory-before.txt"
cd "$NOOP_HOME"
vdot_command=(make emu "CONFIG=$vdot_config" NUM_CORES=1 \
  "JVM_XMX=$vdot_heap" JVM_XSS=8m DISABLE_PERF=1 DISABLE_ALWAYSDB=1 EMU_TRACE=fst -j1)
printf '%q ' "${vdot_command[@]}" > "$vdot_report/command.txt"
printf '\n' >> "$vdot_report/command.txt"
printf 'Build evidence: %s\n' "$vdot_report"
if systemd-run --user --scope --unit="$vdot_unit" \
  -p "MemoryMax=$vdot_limit" -p MemorySwapMax=0 \
  /usr/bin/time -v -o "$vdot_report/time.txt" "${vdot_command[@]}" \
  > "$vdot_report/build.log" 2>&1; then
  vdot_status=0
else
  vdot_status=$?
fi
printf '%s\n' "$vdot_status" > "$vdot_report/exit-status.txt"
systemctl --user show "$vdot_unit.scope" \
  -p Result -p MemoryPeak -p CPUUsageNSec > "$vdot_report/scope.txt" || true
free -b > "$vdot_report/memory-after.txt"
tail -n 15 "$vdot_report/build.log"
exit "$vdot_status"
