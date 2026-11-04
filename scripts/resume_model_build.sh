#!/usr/bin/env bash
# Resume the native build from already generated RTL, in a persistent user unit.
set -euo pipefail
source "$(dirname -- "$0")/env.sh"

if [[ "${1:-}" != --worker ]]; then
  [[ $# == 0 ]] || { printf 'Usage: %s\n' "$0" >&2; exit 2; }
  test -s "$NOOP_HOME/build/rtl/SimTop.sv"
  test -s "$NOOP_HOME/build/generated-src/difftest-dpic.cpp"
  vdot_run_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
  vdot_report="$VDOT_ROOT/reports/model-resume-$vdot_run_id"
  vdot_unit="vdot-model-$vdot_run_id"
  mkdir -p "$vdot_report"
  python3 "$VDOT_ROOT/scripts/source_manifest.py" "$vdot_report/source-before.json"
  printf '%s\n' "$vdot_unit.service" > "$vdot_report/unit.txt"
  # This service keeps running if the calling terminal or chat is disconnected.
  systemd-run --user --unit="$vdot_unit" \
    --working-directory="$VDOT_ROOT" \
    -p "MemoryMax=${VDOT_COMPILE_MEMORY_MAX:-5500M}" -p MemorySwapMax=0 \
    -p "StandardOutput=append:$vdot_report/service.log" -p StandardError=inherit \
    --setenv="VDOT_TRACE_DEPTH=${VDOT_TRACE_DEPTH:-12}" \
    --setenv="VDOT_VERILATOR_OPT=${VDOT_VERILATOR_OPT:-1}" \
    --setenv="VDOT_NATIVE_HEAP_SIZE=${VDOT_NATIVE_HEAP_SIZE:-34359738368}" \
    --setenv="VDOT_NATIVE_FILE_HEAP=${VDOT_NATIVE_FILE_HEAP:-1}" \
    /bin/bash "$VDOT_ROOT/scripts/resume_model_build.sh" --worker "$vdot_report"
  printf 'BUILD_STARTED unit=%s.service report=%s\n' "$vdot_unit" "$vdot_report"
  exit 0
fi

[[ $# == 2 ]] || exit 2
vdot_report=$2
exec >> "$vdot_report/build.log" 2>&1
cd "$NOOP_HOME"
free -b > "$vdot_report/memory-before.txt"
python3 - "$vdot_report" <<'PY'
import hashlib
import json
from pathlib import Path
import sys
report = Path(sys.argv[1])
paths = list(Path('build/rtl').glob('*.sv'))
paths += list(Path('build/generated-src').glob('*'))
digests = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(paths) if p.is_file()}
(report / 'generated-input-sha256.json').write_text(json.dumps(digests, indent=2) + '\n')
PY
vdot_command=(make emu CONFIG=MinimalConfig NUM_CORES=1 DISABLE_PERF=1
  DISABLE_ALWAYSDB=1 WITH_CHISELDB=0 WITH_CONSTANTIN=0 EMU_TRACE=fst
  "VERILATOR=$VDOT_ROOT/scripts/lowmem-bin/verilator" -j1)
printf '%q ' "${vdot_command[@]}" > "$vdot_report/command.txt"
printf '\n' >> "$vdot_report/command.txt"
set +e
/usr/bin/time -v -o "$vdot_report/time.txt" "${vdot_command[@]}"
vdot_status=$?
set -e
if [[ $vdot_status == 0 && ! -x build/emu ]]; then vdot_status=1; fi
printf '%s\n' "$vdot_status" > "$vdot_report/exit-status.txt"
python3 "$VDOT_ROOT/scripts/source_manifest.py" "$vdot_report/source-after.json"
free -b > "$vdot_report/memory-after.txt"
if [[ $vdot_status == 0 ]]; then
  sha256sum build/emu > "$vdot_report/emu.sha256"
  printf 'MODEL_BUILD_COMPLETE\n'
else
  printf 'MODEL_BUILD_FAILED exit=%s\n' "$vdot_status"
fi
exit "$vdot_status"
