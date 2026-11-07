"""Run real-input multi-output GEMV against four equivalent vector kernels."""
import argparse,csv,hashlib,json,os,re,shutil,statistics,subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--emu',type=Path);p.add_argument('--reference',type=Path);p.add_argument('--nemu',type=Path);p.add_argument('--flash',type=Path,required=True);p.add_argument('--shards',type=int,default=9);p.add_argument('--jobs',type=int,default=2);p.add_argument('--resume',type=Path);p.add_argument('--parts');a=p.parse_args()
assert bool(a.emu)!=bool(a.nemu) and bool(a.emu)==bool(a.reference)
assert 1<=a.shards<=36 and 1<=a.jobs<=9
parts=list(map(int,a.parts.split(','))) if a.parts else list(range(a.shards))
assert len(set(parts))==len(parts) and all(0<=part<a.shards for part in parts)
root=Path(__file__).resolve().parents[1]
out=a.resume.resolve(strict=True) if a.resume else root/'reports'/('gemv-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid()))
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
exe=(a.emu or a.nemu).resolve(strict=True);flash=a.flash.resolve(strict=True);ref=a.reference.resolve(strict=True) if a.reference else None
if a.resume:
 bound=json.loads((out/'bindings.json').read_text())
 for path,digest in bound.items():assert h(Path(path))==digest, path
 for path in [exe,flash]+([ref] if ref else []):assert str(path) in bound
 for f in ['examples/gemv_benchmark.c','workloads/start.S','workloads/link.ld','workloads/console.h']:
  assert h(root/f)==h(out/'inputs'/Path(f).name), f
 existing_commands=list(out.glob('part-*/commands.json'))
 assert existing_commands
 for commands in existing_commands:
  assert f'-DGEMV_SHARDS={a.shards}' in json.loads(commands.read_text())['compile']
 control=out/('continuation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid()))
 shutil.copyfile(__file__,control.with_suffix('.py'))
 write(control.with_suffix('.json'),{'parts':parts,'jobs':a.jobs,'shards':a.shards,'runner_sha256':h(control.with_suffix('.py')),'mode':'nemu' if a.nemu else 'rtl_nemu','bindings_sha256':h(out/'bindings.json')})
else:
 (out/'inputs').mkdir(parents=True)
 for f in ['examples/gemv_benchmark.c','scripts/run_gemv_benchmark.py','workloads/start.S','workloads/link.ld','workloads/console.h']:shutil.copyfile(root/f,out/'inputs'/Path(f).name)
 bound={str(f):h(f) for f in [exe,flash,*sorted((out/'inputs').iterdir())]+([ref] if ref else [])}
 write(out/'bindings.json',bound)
print('GEMV_STARTED '+str(out),flush=True)
def run(part):
 d=out/f'part-{part:02d}'
 if d.exists():
  assert a.resume and (d/'exit-status.txt').read_text().strip()=='0', part
  assert (d/'assembly-audit.json').is_file()
  text=re.sub(r'\x1b\[[0-9;]*m','',(d/'run.log').read_text())
  assert 'GEMV_PASS' in text and 'HIT GOOD TRAP' in text and not re.search(r'GEMV_FAIL|GEMV_SENTINEL_FAIL|ABORT|different at pc|HIT BAD TRAP',text)
  if a.emu:assert 'Difftest enabled.' in text and 'dirty: 0' in text
  return text
 d.mkdir();elf=d/'test.elf';binary=d/'test.bin'
 cmd=['riscv64-unknown-elf-gcc','-march=rv64gcv','-mabi=lp64d','-mcmodel=medany','-O2','-fno-tree-vectorize','-ffreestanding','-fno-builtin','-nostdlib','-nostartfiles','-I'+str(out/'inputs'),'-Wl,--no-relax','-Wl,-T,'+str(out/'inputs/link.ld'),f'-DGEMV_SHARD={part}',f'-DGEMV_SHARDS={a.shards}',str(out/'inputs/start.S'),str(out/'inputs/gemv_benchmark.c'),'-o',str(elf)]
 with (d/'build.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=f,check=True)
 subprocess.run(['riscv64-unknown-elf-objcopy','-O','binary',str(elf),str(binary)],check=True)
 dis=subprocess.check_output(['riscv64-unknown-elf-objdump','-d',str(elf)],text=True);(d/'test.dis').write_text(dis)
 audits=[]
 for v in range(4):
  for m in (1,4,8):
   name=f'gemv_{v}_{m}'
   match=re.search(r'^[0-9a-f]+ <'+name+r'>:\n(.*?)(?=\n[0-9a-f]+ <|\Z)',dis,re.M|re.S);assert match,name
   ins=list(re.finditer(r'^\s*([0-9a-f]+):\s+([0-9a-f]+)\s+(.+)$',match[1],re.M))
   counters=[int(i[1],16) for i in ins if re.search(r'\brdcycle\b',i[3])];stores=[int(i[1],16) for i in ins if i[3].startswith('vs1r.v')]
   assert len(counters)==2 and len(stores)==m and all(counters[0]<pc<counters[1] for pc in stores)
   branches=[i for i in ins if i[3].startswith('bnez') and counters[0]<int(i[1],16)<counters[1]]
   assert len(branches)==(2 if v==2 and m==8 else 1)
   loops=[]
   for br in branches:
    target=int(re.search(r'bnez\s+\w+,\s*([0-9a-f]+)',br[3])[1],16)
    loop=[i for i in ins if target<=int(i[1],16)<=int(br[1],16)]
    loads=sum(i[3].startswith('vle8.v') for i in loop);n=m//2 if v==2 and m==8 else m
    assert loads==1+n,(name,loads)
    assert not any(i[3].startswith('vs1r.v') for i in loop)
    assert all(not re.match(r'(?:addi|add|mv)\s+t3,',i[3]) for i in loop)
    custom=sum((int(i[2],16)&0xfc00707f)==(0x0400000b if v==3 else 0x0000000b) for i in loop) if v in (0,3) else 0
    if v in (0,3):assert custom==n
    loops.append({'instructions':len(loop),'vector_loads':loads,'outputs_per_input_block':n,'custom_operations':custom,'begin_pc':hex(target)})
   audits.append({'kernel':name,'cycle_pcs':list(map(hex,counters)),'stores_inside_timing':len(stores),'output_pointer_unmodified_in_loop':True,'loops':loops})
 write(d/'assembly-audit.json',audits)
 sim=[str(exe),'--batch','--flash-image='+str(flash),str(binary)] if a.nemu else [str(exe),'-i',str(binary),'-F',str(flash),'--ram-size=128MB','--diff='+str(ref),'--no-squash','-C','5000000']
 write(d/'commands.json',{'compile':cmd,'run':sim})
 with (d/'run.log').open('w') as f:r=subprocess.run(['/usr/bin/time','-v','-o',str(d/'time.txt'),*sim],cwd=root,stdout=f,stderr=f)
 (d/'exit-status.txt').write_text(str(r.returncode)+'\n');text=re.sub(r'\x1b\[[0-9;]*m','',(d/'run.log').read_text())
 assert r.returncode==0,(part,r.returncode)
 assert 'GEMV_PASS' in text and 'HIT GOOD TRAP' in text and not re.search(r'GEMV_FAIL|GEMV_SENTINEL_FAIL|ABORT|different at pc|HIT BAD TRAP',text)
 if a.emu:assert 'Difftest enabled.' in text and 'dirty: 0' in text
 print('GEMV_PART_PASS '+str(part),flush=True)
 return text
with ThreadPoolExecutor(max_workers=a.jobs) as pool:texts=list(pool.map(run,parts))
if len(parts)!=a.shards:
 print('GEMV_SUBSET_PASSED '+str(parts)+' '+str(out),flush=True)
 raise SystemExit(0)
state=20261107
def rand():
 global state
 state^=(state<<13)&0xffffffff;state^=state>>17;state^=(state<<5)&0xffffffff;state&=0xffffffff
 value=state&255;return value-256 if value>=128 else value
x=[rand() for i in range(512)];w=[[rand() for i in range(512)] for r in range(8)]
rows=[];summary=[]
for line in '\n'.join(texts).splitlines():
 if not line.startswith('GEMV_ROW,'):continue
 values=list(map(int,line.split(',')[1:]));v,m,k=values[:3];cycles=values[3:8];actual=values[8:]
 expected=[sum(x[i]*w[r][i] for i in range(k))&0xffffffff for r in range(m)]
 assert actual==expected and len(cycles)==5 and min(cycles)>0
 rows.extend({'variant':v,'m':m,'k':k,'repeat':i,'cycles':c} for i,c in enumerate(cycles))
 summary.append({'variant':v,'m':m,'k':k,'median':statistics.median(cycles),'min':min(cycles),'max':max(cycles),'results_uint32':actual})
assert len(summary)==36 and len({(r['variant'],r['m'],r['k']) for r in summary})==36
assert sum(int(s) for text in texts for s in re.findall(r'GEMV_PASS samples=\d+ directed=(\d+)',text))==144
comparisons=[]
for m in (1,4,8):
 for k in (32,128,512):
  by={r['variant']:r for r in summary if r['m']==m and r['k']==k};fast=min((1,2),key=lambda v:by[v]['median'])
  comparisons.append({'m':m,'k':k,'rvv8':by[1]['median'],'rvv16':by[2]['median'],'dot_add':by[0]['median'],'acc':by[3]['median'],'selected_rvv':fast,'rvv_over_dot_add':by[fast]['median']/by[0]['median'],'rvv_over_acc':by[fast]['median']/by[3]['median']})
for path,digest in bound.items():assert h(Path(path))==digest
result={'status':'passed','scope':'nemu_standalone' if a.nemu else 'rtl_nemu_difftest','hardware_performance':bool(a.emu),'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'samples':180,'directed_executions':144,'full128_and_unused_sentinel_checked':True,'repeats':5,'warmups_per_group':1,'variants':{'0':'dot+add','1':'RVV8 widening reduction','2':'RVV16 lane accumulation','3':'vdot.acc'},'rvv16_m8_tiling':'two four-output tiles due to 32 vector-register capacity; x reread for second tile','timing':'vector init, shared-x and row-weight loads, loop, accumulation/reduction, one 16-byte output per row, ending fence; host golden outside','groups':summary,'comparisons':comparisons if a.emu else [],'input_bindings':bound}
write(out/'results.json',result)
if a.emu:
 for name,data in [('samples.csv',rows),('comparisons.csv',comparisons)]:
  with (out/name).open('w',newline='') as f:writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
print('GEMV_PASSED '+str(out),flush=True)
print(json.dumps(result['comparisons'],indent=2),flush=True)
