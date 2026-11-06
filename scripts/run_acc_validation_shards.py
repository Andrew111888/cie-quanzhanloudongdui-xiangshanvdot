"""Run disjoint fixed-seed accumulating-dot cases in parallel RTL/NEMU shards."""
import argparse,concurrent.futures,hashlib,json,os,re,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--emu',type=Path);p.add_argument('--reference',type=Path);p.add_argument('--nemu',type=Path);p.add_argument('--flash',type=Path,required=True);p.add_argument('--shards',type=int,default=16);p.add_argument('--jobs',type=int,default=8);a=p.parse_args()
assert bool(a.nemu)!=bool(a.emu) and bool(a.emu)==bool(a.reference) and 1<=a.shards<=1006 and 1<=a.jobs<=16
root=Path(__file__).resolve().parents[1];stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid());out=root/'reports'/('acc-validation-shards-'+stamp);(out/'inputs').mkdir(parents=True)
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
for name in ('examples/acc_validation.c','scripts/run_acc_validation_shards.py','workloads/start.S','workloads/link.ld','workloads/console.h'):shutil.copy2(root/name,out/'inputs'/Path(name).name)
exe=(a.nemu or a.emu).resolve(strict=True);flash=a.flash.resolve(strict=True);ref=a.reference.resolve(strict=True) if a.reference else None
bound={str(p):h(p) for p in [exe,flash,*sorted((out/'inputs').iterdir())]+([ref] if ref else [])}
def next_random(x):
 x^=(x<<13)&0xffffffff;x^=x>>17;x^=(x<<5)&0xffffffff;return x&0xffffffff
state=20261106;states=[];checksums=[];edges=[(1,1),(-1,1),(-128,-128),(-128,127),(127,127),(0,-128)];seeds=[0x12345678,0xfffffff9,0x7fffffff,0x80000000,0xfffffffe,0xdeadbeef]
for case in range(1006):
 states.append(state);aa=[];bb=[]
 for lane in range(16):
  if case<6:x,y=edges[case]
  else:
   state=next_random(state);x=state&255;x=x-256 if x>=128 else x
   state=next_random(state);y=state&255;y=y-256 if y>=128 else y
  aa.append(x);bb.append(y)
 if case<6:old=seeds[case]
 else:state=next_random(state);old=state
 state=next_random(state);state=next_random(state)
 first=lambda values:sum((values[i]&255)<<(8*i) for i in range(4));checksum=0
 for policy in range(2):
  for mode in range(6):
   seed=first(aa) if mode in (1,4) else first(bb) if mode==2 else old
   selected=aa if mode in (3,4) else bb;dot=sum(aa[i]*selected[i] for i in range(8));value=(dot if mode==5 else seed+dot)&0xffffffff
   checksum^=(value+case*17+mode+policy*0x9e3779b9)&0xffffffff
 checksums.append(checksum)
print('ACC_SHARDS_STARTED '+str(out),flush=True)
def run(part):
 begin=part*1006//a.shards;end=(part+1)*1006//a.shards;count=end-begin;directed=max(0,min(end,6)-begin);d=out/f'part-{part:02d}';d.mkdir();elf=d/'test.elf';binary=d/'test.bin'
 flags=[f'-DACC_FIRST_CASE={begin}',f'-DACC_CASE_COUNT={count}',f'-DACC_RANDOM_STATE={states[begin]}u']
 cmd=['riscv64-unknown-elf-gcc','-march=rv64gcv','-mabi=lp64d','-mcmodel=medany','-O2','-fno-tree-vectorize','-ffreestanding','-fno-builtin','-nostdlib','-nostartfiles','-I'+str(out/'inputs'),'-Wl,--no-relax','-Wl,-T,'+str(out/'inputs/link.ld'),*flags,out/'inputs/start.S',out/'inputs/acc_validation.c','-o',elf]
 with (d/'build.log').open('w') as log:subprocess.run(list(map(str,cmd)),check=True,stdout=log,stderr=log)
 subprocess.run(['riscv64-unknown-elf-objcopy','-O','binary',str(elf),str(binary)],check=True)
 simulation=[str(exe),'--batch','--flash-image='+str(flash),str(binary)] if a.nemu else [str(exe),'-i',str(binary),'-F',str(flash),'--ram-size=128MB','--diff='+str(ref),'--no-squash','-C','2000000']
 write(d/'commands.json',{'compile':list(map(str,cmd)),'run':simulation,'first_case':begin,'case_count':count,'rng_state_before_first_case':states[begin]})
 with (d/'run.log').open('w') as log:r=subprocess.run(['/usr/bin/time','-v','-o',str(d/'time.txt'),*simulation],cwd=root,stdout=log,stderr=log)
 (d/'exit-status.txt').write_text(str(r.returncode)+'\n');assert r.returncode==0,(part,r.returncode)
 text=re.sub(r'\x1b\[[0-9;]*m','',(d/'run.log').read_text());match=re.search(r'ACC_VALIDATION_PASS random_cases=(\d+) directed_cases=(\d+) modes=6 tail_policies=2 high_source_pairs=(\d+) chain_instructions=640 illegal_cases=7 checksum=(\d+)',text)
 assert match and list(map(int,match.groups()[:3]))==[count-directed,directed,directed],part
 expected=0
 for v in checksums[begin:end]:expected^=v
 assert int(match[4])==expected and f'ACC_RANGE first={begin} count={count}' in text
 assert 'HIT GOOD TRAP' in text and 'ACC_ILLEGAL_PASS forms=7' in text
 assert not re.search(r'ABORT|ACC_FAIL|ACC_MISMATCH|different at pc|HIT BAD TRAP|CRITICAL ERROR',text,re.I),part
 version=re.search(r'Commit SHA is: ([0-9a-f]+), dirty: ([01])',text)
 if not a.nemu:assert version and version[2]=='0' and 'Difftest enabled.' in text
 row={'part':part,'first_case':begin,'case_count':count,'random_cases':count-directed,'directed_cases':directed,'checksum':expected,'reported_core_commit_prefix':version[1] if version else None,'raw_exit_status':0,'run_log_sha256':h(d/'run.log'),'binary_sha256':h(binary)};write(d/'results.json',{'status':'passed',**row});print('ACC_SHARD_PASS '+str(part),flush=True);return row
with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:rows=list(pool.map(run,range(a.shards)))
ids=[i for r in rows for i in range(r['first_case'],r['first_case']+r['case_count'])];assert ids==list(range(1006))
assert sum(r['random_cases'] for r in rows)==1000 and sum(r['directed_cases'] for r in rows)==6
for name,value in bound.items():assert h(Path(name))==value,name
for f in out.rglob('*'):
 if f.is_file():bound[str(f.resolve())]=h(f)
versions={r['reported_core_commit_prefix'] for r in rows};assert len(versions)==1
receipt={'status':'passed','scope':'nemu_standalone' if a.nemu else 'rtl_nemu_difftest','reported_core_commit_prefix':rows[0]['reported_core_commit_prefix'],'reported_core_dirty':None if a.nemu else 0,'full_core_difftest_completed':not bool(a.nemu),'difftest_enabled':not bool(a.nemu),'random_input_groups':1000,'directed_input_groups':6,'alias_modes':6,'tail_policies':2,'shard_count':a.shards,'jobs':a.jobs,'case_coverage':'global indices 0..1005 exactly once, same unsplit RNG stream','shards':rows,'legal_instruction_executions':1006*12+6+640*a.shards,'chain_instructions_per_shard':640,'illegal_forms_per_shard':7,'input_sha256':bound,'source_snapshot_unchanged':True,'wave_dump_enabled':False}
write(out/'results.json',receipt);print('ACC_SHARDS_PASSED '+str(out),flush=True)
