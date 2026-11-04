#!/usr/bin/env bash
# Require a vector comparator failure, then rerun with the unchanged good REF.
set -euo pipefail
source "$(dirname -- "$0")/env.sh"
[[ $# == 1 ]] || { printf 'Usage: %s /absolute/path/to/fault-reference.so\n' "$0" >&2; exit 2; }
vdot_bad=$(realpath "$1")
vdot_good="$VDOT_ROOT/build/nemu/reference/riscv64-nemu-interpreter-so"
test -f "$vdot_good" && test -f "$vdot_bad"
if cmp -s "$vdot_good" "$vdot_bad"; then
  printf 'Fault REF must differ from the good REF.\n' >&2
  exit 2
fi
unset VDOT_WAVE_BEGIN VDOT_WAVE_END
vdot_run_id=$(date -u +%Y%m%dT%H%M%SZ)-$$
vdot_report="$VDOT_ROOT/reports/fault-check-$vdot_run_id"
mkdir -p "$vdot_report"
sha256sum "$vdot_good" "$vdot_bad" "$NOOP_HOME/build/emu" \
  "$VDOT_ROOT/build/workloads/vdot_smoke.bin" "$VDOT_ROOT/build/workloads/flash.bin" \
  > "$vdot_report/inputs-before.sha256"
printf 'Fault-check evidence: %s\n' "$vdot_report"
VDOT_REF_SO="$vdot_good" bash "$VDOT_ROOT/scripts/run_rtl.sh" vdot_smoke \
  > "$vdot_report/positive-before.log" 2>&1
set +e
VDOT_REF_SO="$vdot_bad" bash "$VDOT_ROOT/scripts/run_rtl.sh" vdot_smoke \
  > "$vdot_report/negative.log" 2>&1
vdot_status=$?
set -e
printf '%s\n' "$vdot_status" > "$vdot_report/negative-exit-status.txt"
python3 - "$VDOT_ROOT" "$vdot_report" <<'PY'
import json
from pathlib import Path
import re
import sys
root, report = map(Path, sys.argv[1:])
driver = (report / 'negative.log').read_text(errors='replace')
match = re.search(r'^RTL evidence: (.+)$', driver, re.M)
if not match:
    raise SystemExit('No RTL run evidence: negative run was not a comparator test')
run = Path(match.group(1)).resolve()
run.relative_to((root / 'reports').resolve())
text = re.sub(r'\x1b\[[0-9;]*m', '', (run / 'run.log').read_text(errors='replace'))
expected = re.search(r'\bv12_low\s+different at pc = 0x[0-9a-fA-F]+,\s*'
                     r'right = 0x0*9,\s*wrong = 0x0*8\b', text)
status = int((report / 'negative-exit-status.txt').read_text())
emu_status = int((run / 'exit-status.txt').read_text())
if status != 1 or emu_status != 1 or not expected or 'ABORT at pc' not in text:
    raise SystemExit('Expected REF=9/DUT=8 vector mismatch, ABORT, and exit 1 were not all observed')
if 'HIT GOOD TRAP' in text:
    raise SystemExit('Negative run unexpectedly reported GOOD TRAP')
commits = re.findall(r'^\[\d+\]\s+commit pc ([0-9a-fA-F]{16}) inst 02a4060b '
                     r'wen 1 dst 12 data [0-9a-fA-F]{16} idx [0-9a-fA-F]{3}([^\r\n]*)$', text, re.M)
if not commits or commits[0][1].strip() not in ('', '<--'):
    raise SystemExit('Missing first vdot commit with an unskipped, non-delayed v12 write')
(report / 'detected-mismatch.json').write_text(json.dumps({
    'rtl_run': str(run), 'observed_line': expected.group(0),
    'exit_status': emu_status, 'field': 'v12_low', 'reference': 9, 'dut': 8,
    'first_vdot_commit_pc': commits[0][0],
}, indent=2) + '\n')
PY
VDOT_REF_SO="$vdot_good" bash "$VDOT_ROOT/scripts/run_rtl.sh" vdot_smoke \
  > "$vdot_report/positive-restored.log" 2>&1
sha256sum --check "$vdot_report/inputs-before.sha256" > "$vdot_report/inputs-unchanged.txt"
printf 'FAULT_CHECK_PASS: positive, vector mismatch, restored positive\n'
