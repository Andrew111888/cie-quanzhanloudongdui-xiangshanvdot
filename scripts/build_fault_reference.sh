#!/usr/bin/env bash
# Build a deliberately wrong REF from an isolated copy, never the live NEMU tree.
set -euo pipefail
source "$(dirname -- "$0")/env.sh"
vdot_original="$NEMU_HOME"
mkdir -p "$VDOT_ROOT/build/fault-injection" "$VDOT_ROOT/build/nemu/fault-reference"
vdot_copy=$(mktemp -d "$VDOT_ROOT/build/fault-injection/nemu-XXXXXX")
vdot_output="$VDOT_ROOT/build/nemu/fault-reference/${vdot_copy##*/}"
mkdir -p "$vdot_output"
python3 - "$vdot_original" "$vdot_copy" "$vdot_output" <<'PY'
import hashlib
import json
from pathlib import Path
import shutil
import sys
original, destination, output = map(Path, sys.argv[1:])
def ignore(directory, names):
    excluded = {'.git', '__pycache__'}
    if Path(directory) == original:
        excluded.add('build')
    return excluded.intersection(names)

shutil.copytree(original, destination, dirs_exist_ok=True, ignore=ignore)
relative = Path('src/isa/riscv64/instr/rvv/vcompute.h')
before = (destination / relative).read_text()
needle = '  vreg_l(id_dest->reg, 0) = (uint32_t)result;'
replacement = '  vreg_l(id_dest->reg, 0) = ((uint32_t)result) ^ UINT32_C(1);'
if before.count(needle) == 0:
    # The experimental family shares one macro body for vdot and vdot.acc.
    needle = '  vreg_l(id_dest->reg, 0) = old_accumulator + (uint32_t)result; \\'
    replacement = '  vreg_l(id_dest->reg, 0) = (old_accumulator + (uint32_t)result) ^ UINT32_C(1); \\'
if before.count(needle) != 1:
    raise SystemExit('Expected exactly one vdot result assignment; no fault applied')
after = before.replace(needle, replacement)
(destination / relative).write_text(after)
record = {'purpose': 'INTENTIONALLY WRONG NEMU REF: vdot low result bit flipped',
          'source_copy': str(destination), 'modified_file': str(relative),
          'original_sha256': hashlib.sha256(before.encode()).hexdigest(),
          'injected_sha256': hashlib.sha256(after.encode()).hexdigest(),
          'replacement': replacement}
(output / 'fault.json').write_text(json.dumps(record, indent=2) + '\n')
PY
export NEMU_HOME="$vdot_copy"
cd "$NEMU_HOME"
make riscv64-xs-kmhv2_defconfig
tools/kconfig/build/conf --defconfig="$VDOT_ROOT/configs/nemu-reference.config" Kconfig
tools/kconfig/build/conf --syncconfig Kconfig
make -j1
cp build/riscv64-nemu-interpreter-so "$vdot_output/riscv64-nemu-interpreter-so"
cp .config "$vdot_output/config"
cp include/generated/autoconf.h "$vdot_output/autoconf.h"
sha256sum "$vdot_output/riscv64-nemu-interpreter-so" > "$vdot_output/artifact.sha256"
python3 - "$vdot_original" "$vdot_output" <<'PY'
import hashlib
import json
from pathlib import Path
import sys
original, output = map(Path, sys.argv[1:])
record = json.loads((output / 'fault.json').read_text())
if hashlib.sha256((original / record['modified_file']).read_bytes()).hexdigest() != record['original_sha256']:
    raise SystemExit('Live NEMU source changed while preparing the fault reference')
PY
printf 'FAULT_REFERENCE_BUILT %s\n' "$vdot_output/riscv64-nemu-interpreter-so"
printf 'This is not a successful Difftest fault-injection run.\n'
