"""Measure disjoint benchmark groups concurrently, retaining each actual raw run."""
import argparse,concurrent.futures,hashlib,json,os,re,shutil,subprocess
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from acc_benchmark_common import audit,summarize
p=argparse.ArgumentParser();p.add_argument('--emu',type=Path);p.add_argument('--reference',type=Path);p.add_argument('--nemu',type=Path);p.add_argument('--flash',type=Path,required=True);p.add_argument('--shards',type=int,default=8);p.add_argument('--jobs',type=int,default=4);a=p.parse_args();assert bool(a.nemu)!=bool(a.emu) and bool(a.emu)==bool(a.reference) and 1<=a.shards<=12 and 1<=a.jobs<=16
root=Path(__file__).resolve().parents[1];stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid());report=root/'reports'/('acc-benchmark-shards-'+stamp);(report/'inputs').mkdir(parents=True)
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
for name in ('examples/acc_benchmark.c','scripts/run_acc_benchmark_shards.py','scripts/acc_benchmark_common.py','workloads/start.S','workloads/link.ld','workloads/console.h'):shutil.copy2(root/name,report/'inputs'/Path(name).name)
exe=(a.nemu or a.emu).resolve(strict=True);flash=a.flash.resolve(strict=True);ref=a.reference.resolve(strict=True) if a.reference else None
source_hashes={str(p):h(p) for p in (report/'inputs').iterdir()};artifacts={str(p):h(p) for p in [exe,flash]+([ref] if ref else [])};artifacts.update(source_hashes)
print('ACC_BENCH_SHARDS_STARTED '+str(report),flush=True)
def run(part):
 d=report/f'part-{part:02d}';d.mkdir();elf=d/'test.elf';binary=d/'test.bin';dis=d/'test.dis'
 flags=[f'-DACC_BENCH_SHARD={part}',f'-DACC_BENCH_SHARDS={a.shards}'];cmd=['riscv64-unknown-elf-gcc','-march=rv64gcv','-mabi=lp64d','-mcmodel=medany','-O2','-fno-tree-vectorize','-ffreestanding','-fno-builtin','-nostdlib','-nostartfiles','-I'+str(report/'inputs'),'-Wl,--no-relax','-Wl,-T,'+str(report/'inputs/link.ld'),*flags,report/'inputs/start.S',report/'inputs/acc_benchmark.c','-o',elf]
 with (d/'build.log').open('w') as stream:subprocess.run(list(map(str,cmd)),check=True,stdout=stream,stderr=stream)
 subprocess.run(['riscv64-unknown-elf-objcopy','-O','binary',elf,binary],check=True)
 with dis.open('w') as stream:subprocess.run(['riscv64-unknown-elf-objdump','-d',elf],check=True,stdout=stream)
 audit(dis.read_text(),d)
 sim=[str(exe),'--batch','--flash-image='+str(flash),str(binary)] if a.nemu else [str(exe),'-i',str(binary),'-F',str(flash),'--ram-size=128MB','--diff='+str(ref),'--no-squash','-C','4000000']
 write(d/'commands.json',{'compile':list(map(str,cmd)),'run':sim,'groups':[i for i in range(36) if i%a.shards==part]})
 with (d/'run.log').open('w') as stream:r=subprocess.run(['/usr/bin/time','-v','-o',str(d/'time.txt'),*sim],cwd=root,stdout=stream,stderr=stream)
 (d/'exit-status.txt').write_text(str(r.returncode)+'\n');assert r.returncode==0,(part,r.returncode)
 text=re.sub(r'\x1b\[[0-9;]*m','',(d/'run.log').read_text());m=re.search(r'ACC_BENCH_PASS long_samples=(\d+) chain_samples=(\d+) full_128bit_results=1',text)
 long_groups=[i for i in range(12) if i%a.shards==part];chain_groups=[i for i in range(12,36) if i%a.shards==part]
 assert m and int(m[1])==5*len(long_groups) and int(m[2])==5*len(chain_groups)
 assert 'HIT GOOD TRAP' in text and not re.search(r'ABORT|different at pc|HIT BAD TRAP|CRITICAL ERROR|mismatch',text,re.I)
 if not a.nemu:assert 'Difftest enabled.' in text and 'dirty: 0' in text
 row={'part':part,'groups':long_groups+chain_groups,'raw_exit_status':0,'long_samples':int(m[1]),'chain_samples':int(m[2]),'run_log_sha256':h(d/'run.log'),'binary_sha256':h(binary)};write(d/'results.json',{'status':'passed',**row});print('ACC_BENCH_SHARD_PASS '+str(part),flush=True);return row
with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:rows=list(pool.map(run,range(a.shards)))
assert sorted(i for r in rows for i in r['groups'])==list(range(36))
assert sum(r['long_samples'] for r in rows)==60 and sum(r['chain_samples'] for r in rows)==120
text='\n'.join((report/f'part-{i:02d}/run.log').read_text() for i in range(a.shards));text=re.sub(r'\x1b\[[0-9;]*m','',text)
(report/'run.log').write_text('Combined actual shard logs; originals remain in part-* directories.\n'+text)
for f in report.rglob('*'):
 if f.is_file():artifacts[str(f.resolve())]=h(f)
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();version=re.search(r'Commit SHA is: ([0-9a-f]+), dirty: ([01])',text)
summarize(report,text,artifacts,source_hashes,version,head,SimpleNamespace(returncode=0),SimpleNamespace(allow_dirty_core=False,engine='nemu' if a.nemu else 'rtl'))
r=json.loads((report/'results.json').read_text());r.update(shard_count=a.shards,jobs=a.jobs,groups=rows,measurement_collection='each of 36 groups executed in exactly one actual simulation, warmup and five repeats per group')
if a.nemu:
 r.update(scope='nemu_standalone',difftest_enabled=False,reported_core_commit_prefix=None,reported_core_dirty=None,performance_numbers_are_hardware=False)
 for f in report.glob('*.csv'):f.unlink()
else:r.update(scope='rtl_nemu_difftest',performance_numbers_are_hardware=True)
write(report/'results.json',r);print('ACC_BENCH_SHARDS_PASSED '+str(report),flush=True)
