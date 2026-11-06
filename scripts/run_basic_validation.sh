#!/usr/bin/env bash
# An explicit six-case supplement; existing acceptance workloads stay unchanged.
set -euo pipefail
source "$(dirname -- "$0")/env.sh"
if [[ $# != 2 ]]; then
  printf 'Usage: bash scripts/run_basic_validation.sh <emu> <reference.so>\n' >&2
  exit 2
fi
vdot_basic_emu=$(realpath -- "$1")
vdot_basic_ref=$(realpath -- "$2")
test -x "$vdot_basic_emu"
test -f "$vdot_basic_ref"
vdot_basic_run="$VDOT_ROOT/reports/basic-validation-$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir -p "$vdot_basic_run/inputs" "$vdot_basic_run/workload"
cp "$VDOT_ROOT/examples/vdot_basic.c" "$VDOT_ROOT/workloads/start.S" \
  "$VDOT_ROOT/workloads/link.ld" "$VDOT_ROOT/workloads/console.h" "$vdot_basic_run/inputs/"
cp "$VDOT_ROOT/build/workloads/flash.bin" "$vdot_basic_run/workload/flash.bin"
python3 "$VDOT_ROOT/scripts/source_manifest.py" "$vdot_basic_run/source-before.json"
vdot_basic_build=(riscv64-unknown-elf-gcc -march=rv64gcv -mabi=lp64d -mcmodel=medany \
  -O2 -fno-tree-vectorize -ffreestanding -fno-builtin -nostdlib -nostartfiles \
  -I"$vdot_basic_run/inputs" -Wl,--no-relax -Wl,-T,"$vdot_basic_run/inputs/link.ld" \
  "$vdot_basic_run/inputs/start.S" "$vdot_basic_run/inputs/vdot_basic.c" \
  -o "$vdot_basic_run/workload/vdot_basic.elf")
printf '%q ' "${vdot_basic_build[@]}" > "$vdot_basic_run/build-command.txt"
printf '\n' >> "$vdot_basic_run/build-command.txt"
"${vdot_basic_build[@]}" > "$vdot_basic_run/build.log" 2>&1
riscv64-unknown-elf-objcopy -O binary "$vdot_basic_run/workload/vdot_basic.elf" "$vdot_basic_run/workload/vdot_basic.bin"
riscv64-unknown-elf-objdump -d "$vdot_basic_run/workload/vdot_basic.elf" > "$vdot_basic_run/workload/vdot_basic.dis"
vdot_basic_command=("$vdot_basic_emu" -i "$vdot_basic_run/workload/vdot_basic.bin" \
  -F "$vdot_basic_run/workload/flash.bin" --ram-size=128MB "--diff=$vdot_basic_ref" \
  --no-squash -C 1000000)
printf '%q ' "${vdot_basic_command[@]}" > "$vdot_basic_run/command.txt"
printf '\n' >> "$vdot_basic_run/command.txt"
sha256sum "$vdot_basic_emu" "$vdot_basic_ref" "$vdot_basic_run/workload/vdot_basic.bin" \
  "$vdot_basic_run/workload/flash.bin" "$VDOT_ROOT/examples/vdot_basic.c" \
  "$VDOT_ROOT/scripts/run_basic_validation.sh" > "$vdot_basic_run/artifacts.sha256"
printf 'Basic validation evidence: %s\n' "$vdot_basic_run"
vdot_basic_status=0
systemd-run --user --scope --unit="vdot-basic-$(date -u +%Y%m%dT%H%M%SZ)-$$" \
  -p MemoryMax=3G -p MemorySwapMax=0 /usr/bin/time -v -o "$vdot_basic_run/time.txt" \
  "${vdot_basic_command[@]}" > "$vdot_basic_run/run.log" 2>&1 || vdot_basic_status=$?
printf '%s\n' "$vdot_basic_status" > "$vdot_basic_run/exit-status.txt"
cat "$vdot_basic_run/run.log"
test "$vdot_basic_status" == 0
sha256sum --check "$vdot_basic_run/artifacts.sha256" > "$vdot_basic_run/artifacts-after.txt"
python3 "$VDOT_ROOT/scripts/check_run.py" "$vdot_basic_run/run.log" VDOT_BASIC_PASS
python3 "$VDOT_ROOT/scripts/source_manifest.py" "$vdot_basic_run/source-after.json"
python3 - "$vdot_basic_run" <<'PY'
from pathlib import Path
import hashlib,json,re,sys
p=Path(sys.argv[1]); before=json.loads((p/'source-before.json').read_text());after=json.loads((p/'source-after.json').read_text())
assert before['project_head']==after['project_head']
assert before['project_files_sha256']==after['project_files_sha256']
assert before['repositories']==after['repositories']
text=re.sub(r'\x1b\[[0-9;]*m','',(p/'run.log').read_text())
assert 'Difftest enabled.' in text
pattern=r'^BASIC_CASE name=(\w+) a=(-?\d+) b=(-?\d+) count=8 expected=(-?\d+) actual=(-?\d+) vd=([0-9a-f]{32}) PASS$'
rows=re.findall(pattern,text,re.M)
assert len(rows)==6
records=[]
for name,a,b,want,actual,vd in rows:
    a,b,want,actual=map(int,(a,b,want,actual))
    assert want==actual==8*a*b
    assert int(vd,16)==(want & 0xffffffff)
    records.append({'name':name,'a':a,'b':b,'count':8,'expected':want,'actual':actual,'vd_hex':vd,'status':'passed'})
receipt={'status':'passed','source_project_head':before['project_head'],'source_unchanged':True,'cases':records,
         'difftest_enabled':True,'raw_exit_status':0,'run_log_sha256':hashlib.sha256((p/'run.log').read_bytes()).hexdigest(),
         'note':'Supplemental workload, executed with explicitly selected previously built RTL emulator and NEMU reference. It does not claim a new hardware build.'}
(p/'cases.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print('BASIC_VALIDATION_VERIFIED',p)
PY
