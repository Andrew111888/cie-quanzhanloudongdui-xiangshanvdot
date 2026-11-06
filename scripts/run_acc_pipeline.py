"""Validate accumulating dot products across bursts, producers and branches."""
import argparse,hashlib,json,os,re,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--emu',type=Path);p.add_argument('--reference',type=Path);p.add_argument('--nemu',type=Path);a=p.parse_args()
assert bool(a.nemu)!=bool(a.emu) and bool(a.emu)==bool(a.reference)
root=Path(__file__).resolve().parents[1];stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid())
out=root/'reports'/('acc-pipeline-'+stamp);(out/'inputs').mkdir(parents=True);(out/'workload').mkdir();commands=[]
h=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
def run(argv,**kw):
 commands.append([str(x) for x in argv]);(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');return subprocess.run(commands[-1],cwd=root,check=True,**kw)
for name in ('examples/acc_pipeline.c','scripts/run_acc_pipeline.py','workloads/start.S','workloads/link.ld','workloads/console.h','workloads/flash.S'):shutil.copy2(root/name,out/'inputs'/Path(name).name)
elf=out/'workload/acc-pipeline.elf';binary=elf.with_suffix('.bin');flash=out/'workload/flash.bin'
with (out/'build.log').open('w') as log:
 run(['riscv64-unknown-elf-gcc','-march=rv64gcv','-mabi=lp64d','-mcmodel=medany','-O2','-fno-tree-vectorize','-ffreestanding','-fno-builtin','-nostdlib','-nostartfiles','-I'+str(out/'inputs'),'-Wl,--no-relax','-Wl,-T,'+str(out/'inputs/link.ld'),out/'inputs/start.S',out/'inputs/acc_pipeline.c','-o',elf],stdout=log,stderr=log)
 run(['riscv64-unknown-elf-objcopy','-O','binary',elf,binary])
 run(['riscv64-unknown-elf-gcc','-march=rv64gc','-mabi=lp64d','-nostdlib','-nostartfiles','-Wl,-Ttext=0x10000000',out/'inputs/flash.S','-o',out/'workload/flash.elf'],stdout=log,stderr=log)
 run(['riscv64-unknown-elf-objcopy','-O','binary',out/'workload/flash.elf',flash])
with elf.with_suffix('.dis').open('w') as stream:run(['riscv64-unknown-elf-objdump','-d',elf],stdout=stream)
exe=(a.nemu or a.emu).resolve(strict=True);inputs=[exe,binary,flash,*sorted((out/'inputs').iterdir())]
if a.reference:inputs.append(a.reference.resolve(strict=True))
hashes={str(x):h(x) for x in inputs};(out/'artifacts.json').write_text(json.dumps(hashes,indent=2)+'\n')
command=[exe,'--batch','--flash-image='+str(flash),binary] if a.nemu else [exe,'-i',binary,'-F',flash,'--ram-size=128MB','--diff='+str(a.reference.resolve()),'--no-squash','-C','4000000']
commands.append([str(x) for x in command]);(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');print('ACC_PIPELINE_STARTED '+str(out),flush=True)
with (out/'run.log').open('w') as stream:r=subprocess.run(['systemd-run','--user','--scope','--unit=acc-pipeline-'+stamp,'-p','MemoryMax=2500M','-p','MemorySwapMax=0','/usr/bin/time','-v','-o',str(out/'time.txt'),*map(str,command)],cwd=root,stdout=stream,stderr=stream)
(out/'exit-status.txt').write_text(str(r.returncode)+'\n');assert r.returncode==0
text=re.sub(r'\x1b\[[0-9;]*m','',(out/'run.log').read_text());m=re.search(r'ACC_PIPELINE_PASS bursts=64 acc_instructions=1664 taken=(\d+) not_taken=(\d+) checksum=(\d+)',text);assert m and 'HIT GOOD TRAP' in text
assert int(m[1])+int(m[2])==64 and min(int(m[1]),int(m[2]))>0
assert not re.search(r'ABORT|different at pc|HIT BAD TRAP|mismatch|CRITICAL ERROR',text,re.I)
if a.emu:assert 'Difftest enabled.' in text and 'dirty: 0' in text
for name,value in hashes.items():assert h(Path(name))==value
receipt={'status':'passed','scope':'nemu_standalone' if a.nemu else 'rtl_nemu_difftest','raw_exit_status':0,'acc_instructions':1664,'bursts':64,'taken':int(m[1]),'not_taken':int(m[2]),'checksum':int(m[3]),'checks':['eight independent destinations with distinct old values','vadd producer','16-step aliased accumulator/source chain','both branch outcomes and untouched sentinel'],'input_sha256':hashes,'run_log_sha256':h(out/'run.log'),'internal_flush_timing_claimed':False,'core_dirty':None if a.nemu else 0}
(out/'results.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n');print('ACC_PIPELINE_PASSED '+str(out),flush=True)
