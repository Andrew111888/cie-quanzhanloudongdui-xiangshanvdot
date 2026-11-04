#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/env.sh"

vdot_config=${VDOT_CONFIG:-MinimalConfig}
vdot_heap=${VDOT_JAVA_HEAP:-8G}
vdot_chisel_limit=${VDOT_BUILD_MEMORY_MAX:-4800M}
vdot_firtool_limit=${VDOT_FIRTOOL_MEMORY_MAX:-5500M}
vdot_compile_limit=${VDOT_COMPILE_MEMORY_MAX:-5500M}
vdot_trace=${VDOT_EMU_TRACE-fst}
vdot_firtool=${VDOT_FIRTOOL:-$HOME/.cache/llvm-firtool/1.62.1/bin/firtool}
vdot_run_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
vdot_report="$VDOT_ROOT/reports/vdot-build-$vdot_run_id"
mkdir -p "$vdot_report"
test -x "$vdot_firtool" || { printf 'Missing pinned firtool: %s\n' "$vdot_firtool" >&2; exit 2; }
export PATH="$VDOT_ROOT/scripts/lowmem-bin:$PATH"
export JAVA_TOOL_OPTIONS='-XX:ActiveProcessorCount=2 -XX:+UseSerialGC'
vdot_backing=${VDOT_HEAP_BACKING_DIR-$VDOT_ROOT/build/jvm-heap}
if [[ -n "$vdot_backing" ]]; then
  mkdir -p "$vdot_backing"
  export JAVA_TOOL_OPTIONS="$JAVA_TOOL_OPTIONS -XX:AllocateHeapAt=\"$vdot_backing\""
fi

python3 "$VDOT_ROOT/scripts/source_manifest.py" "$vdot_report/source-before.json"
free -b > "$vdot_report/memory-before.txt"
"$vdot_firtool" --version > "$vdot_report/firtool-version.txt"
printf '%s\n' "$JAVA_TOOL_OPTIONS" > "$vdot_report/java-options.txt"
printf 'Build evidence: %s\n' "$vdot_report"

run_stage() {
  local vdot_stage=$1 vdot_limit=$2
  shift 2
  local vdot_unit="vdot-$vdot_run_id-$vdot_stage" vdot_status
  printf '%q ' "$@" > "$vdot_report/$vdot_stage-command.txt"
  printf '\n' >> "$vdot_report/$vdot_stage-command.txt"
  printf 'Stage: %s\n' "$vdot_stage"
  if systemd-run --user --scope --unit="$vdot_unit" \
    -p "MemoryMax=$vdot_limit" -p MemorySwapMax=0 \
    /usr/bin/time -v -o "$vdot_report/$vdot_stage-time.txt" "$@" \
    > "$vdot_report/$vdot_stage.log" 2>&1; then
    vdot_status=0
  else
    vdot_status=$?
  fi
  printf '%s\n' "$vdot_status" > "$vdot_report/$vdot_stage-exit-status.txt"
  systemctl --user show "$vdot_unit.scope" -p Result -p MemoryPeak -p CPUUsageNSec \
    > "$vdot_report/$vdot_stage-scope.txt" || true
  tail -n 12 "$vdot_report/$vdot_stage.log"
  return "$vdot_status"
}

cd "$NOOP_HOME"
# Keep the Java process and native firtool out of each other's memory budget.
run_stage chisel "$vdot_chisel_limit" mill -i -j 1 \
  "-Djvm-xmx=$vdot_heap" -Djvm-xss=8m xiangshan.test.runMain top.XiangShanSim \
  --target-dir build/rtl --config "$vdot_config" --num-cores 1 --issue E.b \
  --disable-perf --disable-alwaysdb --enable-difftest --target chirrtl --full-stacktrace

sha256sum build/rtl/SimTop.fir > "$vdot_report/fir.sha256"
run_stage firtool "$vdot_firtool_limit" "$vdot_firtool" build/rtl/SimTop.fir \
  --format=fir --split-verilog -o build/rtl --mlir-disable-threading \
  --repl-seq-mem --repl-seq-mem-file=SimTop.sv.conf -O=release \
  --disable-annotation-unknown \
  --lowering-options=explicitBitcast,disallowLocalVariables,disallowPortDeclSharing,locationInfoStyle=none

bash scripts/gen_sep_mem.sh ./scripts/vlsi_mem_gen build/rtl/SimTop.sv.conf build/rtl \
  > "$vdot_report/sram-models.log" 2>&1
# Match the simulation-only postprocessing in the pinned XiangShan Makefile.
python3 - <<'PY'
from pathlib import Path
for path in Path('build/rtl').glob('*.sv'):
    text = path.read_text()
    updated = text.replace('$fatal', 'xs_assert_v2(`__FILE__, `__LINE__)')
    updated = updated.replace('$error(', "$fwrite(32'h80000002, ")
    if updated != text:
        path.write_text(updated)
PY

vdot_compile_env=()
vdot_verilator_option=("VERILATOR=$VDOT_ROOT/scripts/lowmem-bin/verilator")
if [[ "${VDOT_USE_JEMALLOC:-0}" == 1 ]]; then
  vdot_jemalloc=${VDOT_JEMALLOC:-/usr/lib/x86_64-linux-gnu/libjemalloc.so.2}
  test -f "$vdot_jemalloc" || { printf 'Missing jemalloc: %s\n' "$vdot_jemalloc" >&2; exit 2; }
  vdot_compile_env=(env "LD_PRELOAD=$vdot_jemalloc" \
    MALLOC_CONF=narenas:1,dirty_decay_ms:0,muzzy_decay_ms:0,retain:false)
fi
run_stage compile "$vdot_compile_limit" "${vdot_compile_env[@]}" make emu \
  "CONFIG=$vdot_config" NUM_CORES=1 DISABLE_PERF=1 DISABLE_ALWAYSDB=1 \
  WITH_CHISELDB=0 WITH_CONSTANTIN=0 "${vdot_verilator_option[@]}" "EMU_TRACE=$vdot_trace" -j1

test -x build/emu
sha256sum build/emu > "$vdot_report/emu.sha256"
python3 "$VDOT_ROOT/scripts/source_manifest.py" "$vdot_report/source-after.json"
python3 - "$vdot_report" <<'PY'
import json
from pathlib import Path
import sys
directory = Path(sys.argv[1])
before = json.loads((directory / 'source-before.json').read_text())
after = json.loads((directory / 'source-after.json').read_text())
if before['repositories'] != after['repositories'] or before['project_files_sha256'] != after['project_files_sha256']:
    raise SystemExit('Source identity changed during the build; do not use this build as final evidence.')
PY
free -b > "$vdot_report/memory-after.txt"
printf 'BUILD_COMPLETE %s\n' "$vdot_report"
