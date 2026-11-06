"""Snapshot and validate experimental accumulating dot products on NEMU or RTL."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--emu', type=Path)
parser.add_argument('--reference', type=Path)
parser.add_argument('--nemu', type=Path)
parser.add_argument('--flash', type=Path)
parser.add_argument('--build-only', action='store_true')
parser.add_argument('--require-clean', action='store_true')
args = parser.parse_args()
if not args.build_only:
    assert bool(args.nemu) != bool(args.emu), 'Select --nemu or --emu/--reference'
    assert bool(args.emu) == bool(args.reference)
root = Path(__file__).resolve().parents[1]
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + str(os.getpid())
report = root / 'reports' / ('acc-validation-' + stamp)
(report / 'inputs').mkdir(parents=True)
(report / 'workload').mkdir()
sources = [root/'examples/acc_validation.c', root/'scripts/run_acc_validation.py',
           *(root/'workloads'/s for s in ('start.S','link.ld','console.h','flash.S'))]
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source_hashes = {str(p): digest(p) for p in sources}
for p in sources:
    shutil.copy2(p, report/'inputs'/p.name)
commands = []


def run(argv, **kwargs):
    commands.append(list(map(str, argv)))
    (report/'commands.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2)+'\n')
    return subprocess.run(list(map(str, argv)), cwd=root, check=True, **kwargs)


elf = report/'workload/acc-validation.elf'
binary = elf.with_suffix('.bin')
flash = report/'workload/flash.bin'
with (report/'build.log').open('w') as log:
    run(['riscv64-unknown-elf-gcc','-march=rv64gcv','-mabi=lp64d','-mcmodel=medany',
         '-O2','-fno-tree-vectorize','-ffreestanding','-fno-builtin','-nostdlib','-nostartfiles',
         '-I'+str(report/'inputs'),'-Wl,--no-relax','-Wl,-T,'+str(report/'inputs/link.ld'),
         report/'inputs/start.S',report/'inputs/acc_validation.c','-o',elf], stdout=log, stderr=log)
    if args.flash:
        shutil.copy2(args.flash.resolve(strict=True), flash)
    else:
        run(['riscv64-unknown-elf-gcc','-march=rv64gc','-mabi=lp64d','-nostdlib','-nostartfiles',
             '-Wl,-Ttext=0x10000000',report/'inputs/flash.S','-o',report/'workload/flash.elf'],
            stdout=log, stderr=log)
        run(['riscv64-unknown-elf-objcopy','-O','binary',report/'workload/flash.elf',flash])
run(['riscv64-unknown-elf-objcopy','-O','binary',elf,binary])
with elf.with_suffix('.dis').open('w') as stream:
    run(['riscv64-unknown-elf-objdump','-d',elf], stdout=stream)
dis = elf.with_suffix('.dis').read_text()
instructions = [int(m,16) for m in re.findall(r'^\s*[0-9a-f]+:\s+([0-9a-f]{8})\s', dis, re.M)]
counts = {'static_acc_encodings':sum((word & 0xfc00707f)==0x0400000b for word in instructions),
          'static_original_dot_encodings':sum((word & 0xfc00707f)==0x0000000b for word in instructions),
          'static_masked_acc_encodings':sum((word & 0xfe00707f)==0x0400000b for word in instructions)}
assert counts['static_acc_encodings'] >= 10 and counts['static_original_dot_encodings'] >= 1
assert counts['static_masked_acc_encodings'] >= 1
(report/'assembly-audit.json').write_text(json.dumps(counts, indent=2)+'\n')
head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
source_record = {'project_head_at_preparation':head,'source_snapshot_sha256':source_hashes,
                 'scope':'new accumulating dot workload; source snapshots and executable inputs bound independently'}
(report/'source.json').write_text(json.dumps(source_record, ensure_ascii=False, indent=2)+'\n')
print('ACC_VALIDATION_PREPARED '+str(report), flush=True)
if args.build_only:
    (report/'results.json').write_text(json.dumps({'status':'workload_built_not_executed','assembly_audit':counts},indent=2)+'\n')
    raise SystemExit(0)

if args.nemu:
    executable = args.nemu.resolve(strict=True)
    command = [str(executable),'--batch','--flash-image='+str(flash),str(binary)]
    scope = 'nemu_standalone'
    inputs = [executable,binary,flash,*sorted((report/'inputs').iterdir())]
else:
    executable = args.emu.resolve(strict=True)
    reference = args.reference.resolve(strict=True)
    command = [str(executable),'-i',str(binary),'-F',str(flash),'--ram-size=128MB',
               '--diff='+str(reference),'--no-squash','-C','10000000']
    scope = 'rtl_nemu_difftest'
    inputs = [executable,reference,binary,flash,*sorted((report/'inputs').iterdir())]
hashes = {str(p):digest(p) for p in inputs}
(report/'artifacts.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2)+'\n')
commands.append(command)
(report/'commands.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2)+'\n')
print('ACC_VALIDATION_STARTED '+scope+' '+str(report), flush=True)
with (report/'run.log').open('w') as stream:
    result = subprocess.run(['systemd-run','--user','--scope','--unit=vdot-acc-validation-'+stamp,
                             '-p','MemoryMax=2500M','-p','MemorySwapMax=0',
                             '/usr/bin/time','-v','-o',str(report/'time.txt'),*command],
                            cwd=root,stdout=stream,stderr=stream)
(report/'exit-status.txt').write_text(str(result.returncode)+'\n')
assert result.returncode == 0
text = re.sub(r'\x1b\[[0-9;]*m','',(report/'run.log').read_text())
marker = re.search(r'^ACC_VALIDATION_PASS random_cases=1000 directed_cases=6 modes=6 tail_policies=2 high_source_pairs=6 chain_instructions=640 illegal_cases=7 checksum=(\d+)$',text,re.M)
assert marker and 'HIT GOOD TRAP' in text
assert not re.search(r'ACC_FAIL|ACC_MISMATCH|ABORT|different at pc|HIT BAD TRAP|CRITICAL ERROR|mismatch',text,re.I)
assert 'ACC_ILLEGAL_PASS forms=7 destination_and_vstart_preserved=1 ordinary_tval=123' in text
for chains in (1,4):
    assert f'ACC_CHAIN_PASS chains={chains} iterations=128' in text
expected_seeds=[0x12345678,0xfffffff9,0x7fffffff,0x80000000,0xfffffffe,0xdeadbeef]
edges=[(1,1),(-1,1),(-128,-128),(-128,127),(127,127),(0,-128)]
directed=[tuple(map(int,row)) for row in re.findall(r'^ACC_CASE,(\d+),(\d+),(\d+),(\d+)$',text,re.M)]
assert len(directed)==6
for n,seed,want,actual in directed:
    assert n in range(6) and seed==expected_seeds[n]
    assert want==actual==(seed+8*edges[n][0]*edges[n][1])&0xffffffff


def next_random(state):
    state ^= (state << 13)&0xffffffff
    state ^= state >> 17
    state ^= (state << 5)&0xffffffff
    return state&0xffffffff


state=20261106
checksum=0
for case in range(1006):
    a=[];b=[]
    for lane in range(16):
        if case<6:
            x,y=edges[case]
        else:
            state=next_random(state);x=state&255;x=x-256 if x>=128 else x
            state=next_random(state);y=state&255;y=y-256 if y>=128 else y
        a.append(x);b.append(y)
    if case<6:
        old=expected_seeds[case]
    else:
        state=next_random(state);old=state
    state=next_random(state);state=next_random(state)
    first=lambda values:sum((values[i]&255)<<(8*i) for i in range(4))
    for policy in range(2):
        for mode in range(6):
            seed=first(a) if mode in (1,4) else first(b) if mode==2 else old
            chosen=a if mode in (3,4) else b
            partial=sum(a[i]*chosen[i] for i in range(8))
            value=(partial if mode==5 else seed+partial)&0xffffffff
            checksum ^= (value+case*17+mode+policy*0x9e3779b9)&0xffffffff
assert int(marker[1])==checksum
version=re.search(r'Commit SHA is: ([0-9a-f]+), dirty: ([01])',text)
if scope=='rtl_nemu_difftest':
    assert 'Difftest enabled.' in text and version is not None
    if args.require_clean:assert version[2]=='0'
assert all(digest(Path(p))==value for p,value in hashes.items())
assert all(digest(Path(p))==value for p,value in source_hashes.items())
receipt={'status':'passed','scope':scope,'directory':str(report),'project_head_at_preparation':head,
         'raw_exit_status':result.returncode,'difftest_enabled':scope=='rtl_nemu_difftest',
         'full_core_difftest_completed':scope=='rtl_nemu_difftest',
         'reported_core_commit_prefix':version[1] if version else None,
         'reported_core_dirty':int(version[2]) if version else None,
         'wave_dump_enabled':False,'random_input_groups':1000,'directed_input_groups':6,'alias_modes':6,
         'tail_policies':2,'high_source_pairs':6,'chain_instructions':640,'illegal_forms':7,
         'legal_instruction_executions':1006*6*2+6+640,'directed':directed,'checksum':checksum,
         'input_sha256':hashes,'source_snapshot_unchanged':True,'run_log_sha256':digest(report/'run.log')}
(report/'results.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print('ACC_VALIDATION_PASSED '+str(report),flush=True)
