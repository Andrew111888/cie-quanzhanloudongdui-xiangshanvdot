#!/usr/bin/env bash
# Run after build_emu.sh completes; optionally target another independent root.
main() {
set -euo pipefail
vdot_target=${1:-$(cd -- "$(dirname -- "$0")/.." && pwd)}
source "$vdot_target/scripts/env.sh"
cd "$VDOT_ROOT"
vdot_acceptance="$VDOT_ROOT/reports/acceptance-$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir -p "$vdot_acceptance"
printf 'ACCEPTANCE_STARTED %s\n' "$vdot_acceptance"
python3 scripts/source_manifest.py "$vdot_acceptance/source-before.json"
python3 scripts/check_patches.py > "$vdot_acceptance/patch-replay.log" 2>&1
python3 -m unittest discover -s tests -v > "$vdot_acceptance/python-tests.log" 2>&1
python3 scripts/check_reference_abi.py build/nemu/reference/riscv64-nemu-interpreter-so \
  --expected-result 8 > "$vdot_acceptance/reference-abi.log" 2>&1
VDOT_WAVE_BEGIN=0 VDOT_WAVE_END=15000 bash scripts/run_rtl.sh vadd_test \
  > "$vdot_acceptance/vadd.log" 2>&1
bash scripts/run_rtl.sh vdot_smoke > "$vdot_acceptance/smoke.log" 2>&1
bash scripts/run_rtl.sh register_test > "$vdot_acceptance/register.log" 2>&1
bash scripts/build_fault_reference.sh > "$vdot_acceptance/fault-build.log" 2>&1
vdot_fault=$(sed -n 's/^FAULT_REFERENCE_BUILT //p' "$vdot_acceptance/fault-build.log")
test -f "$vdot_fault"
bash scripts/run_fault_check.sh "$vdot_fault" > "$vdot_acceptance/fault-check.log" 2>&1

# Arithmetic random inputs, distinct pipeline bursts and benchmark sampling are
# independent. Their binaries and reference library remain immutable throughout.
bash scripts/run_rtl.sh vdot_test > "$vdot_acceptance/random.log" 2>&1 &
vdot_random_pid=$!
bash scripts/run_rtl.sh pipeline_test > "$vdot_acceptance/pipeline.log" 2>&1 &
vdot_pipeline_pid=$!
bash scripts/run_rtl.sh benchmark > "$vdot_acceptance/benchmark.log" 2>&1 &
vdot_bench_pid=$!
VDOT_WAVE_BEGIN=0 VDOT_WAVE_END=12000 bash scripts/run_rtl.sh latency_probe \
  > "$vdot_acceptance/latency.log" 2>&1 &
vdot_latency_pid=$!
vdot_fail=0
for vdot_pid in "$vdot_random_pid" "$vdot_pipeline_pid" "$vdot_bench_pid" "$vdot_latency_pid"; do
  wait "$vdot_pid" || vdot_fail=1
done
test "$vdot_fail" = 0
vdot_vadd=$(sed -n 's/^RTL evidence: //p' "$vdot_acceptance/vadd.log")
vdot_latency=$(sed -n 's/^RTL evidence: //p' "$vdot_acceptance/latency.log")
vdot_bench=$(sed -n 's/^RTL evidence: //p' "$vdot_acceptance/benchmark.log")
vdot_pipeline=$(sed -n 's/^RTL evidence: //p' "$vdot_acceptance/pipeline.log")
python3 scripts/performance_report.py "$vdot_bench/run.log" --engine rtl \
  --output "$vdot_acceptance/performance.md"
python3 scripts/extract_wave_events.py "$vdot_vadd/wave.fst" --output "$vdot_acceptance/vadd-events"
python3 scripts/extract_wave_events.py "$vdot_latency/wave.fst" --output "$vdot_acceptance/latency-events"
python3 scripts/analyze_wave.py --vadd-events "$vdot_acceptance/vadd-events" \
  --latency-events "$vdot_acceptance/latency-events" --output "$vdot_acceptance/wave-analysis"

if VDOT_MAX_CYCLES=28000 VDOT_WAVE_BEGIN=14000 VDOT_WAVE_END=27000 \
  bash scripts/run_rtl.sh pipeline_test > "$vdot_acceptance/pipeline-diagnostic.log" 2>&1; then
  printf 'Diagnostic unexpectedly finished the entire workload before its budget\n' >&2
  return 1
else
  vdot_probe_status=$?
fi
test "$vdot_probe_status" = 1
vdot_probe=$(sed -n 's/^RTL evidence: //p' "$vdot_acceptance/pipeline-diagnostic.log")
python3 - "$vdot_probe" <<'PY'
import json,re,sys
from pathlib import Path
p=Path(sys.argv[1]);text=(p/'run.log').read_text(errors='replace')
assert (p/'exit-status.txt').read_text().strip()=='0'
assert 'EXCEEDING CYCLE/INSTR LIMIT' in text and 'Difftest enabled.' in text
assert not re.search(r'ABORT|different at pc|HIT BAD TRAP|CRITICAL ERROR|Assertion.*fail|mismatch',text,re.I)
(p/'diagnostic-purpose.json').write_text(json.dumps({'purpose':'bounded FST only','functional_pass':False,'expected_budget_stop':28000},indent=2)+'\n')
PY
python3 scripts/extract_wave_events.py "$vdot_probe/wave.fst" \
  --output "$vdot_acceptance/pipeline-events"
# The verified pipeline analyzer may be newer than this frozen build checkout;
# execute the exact entry-point copy shipped with this acceptance driver.
vdot_driver_root=$(cd -- "$(dirname -- "$0")/.." && pwd)
python3 "$vdot_driver_root/scripts/analyze_pipeline_wave.py" \
  --events "$vdot_acceptance/pipeline-events" --full-run "$vdot_pipeline" \
  --output "$vdot_acceptance/pipeline-analysis"
python3 scripts/source_manifest.py "$vdot_acceptance/source-after.json"
python3 - "$vdot_acceptance" "$0" <<'PY'
import hashlib,json,sys
from pathlib import Path
p=Path(sys.argv[1]);before=json.loads((p/'source-before.json').read_text());after=json.loads((p/'source-after.json').read_text())
assert before['repositories']==after['repositories']
assert before['project_files_sha256']==after['project_files_sha256']
records={}
for label in ('vadd','smoke','register','random','pipeline','benchmark','latency'):
 line=next(s for s in (p/(label+'.log')).read_text().splitlines() if s.startswith('RTL evidence: '))
 d=Path(line.removeprefix('RTL evidence: '))
 assert (d/'exit-status.txt').read_text().strip()=='0'
 records[label]=str(d)
driver=Path(sys.argv[2]).resolve()
result={'status':'passed','source_project_head':before['project_head'],'source_unchanged':True,
        'rtl_runs':records,'driver':str(driver),'driver_sha256':hashlib.sha256(driver.read_bytes()).hexdigest(),
        'fault_check_log':str(p/'fault-check.log'),'diagnostic_is_functional_pass':False,
        'remaining':'final report/video/package binding and submission'}
(p/'acceptance.json').write_text(json.dumps(result,indent=2)+'\n')
PY
printf 'ACCEPTANCE_COMPLETE %s\n' "$vdot_acceptance"
}
main "$@"; exit "$?"
