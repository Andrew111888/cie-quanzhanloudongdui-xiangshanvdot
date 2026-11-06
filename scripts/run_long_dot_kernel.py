"""Compile a snapshot and measure true cross-block int8 dot products on RTL."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--emu',type=Path,required=True)
parser.add_argument('--reference',type=Path,required=True)
parser.add_argument('--flash',type=Path,required=True)
parser.add_argument('--build-only',action='store_true')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid())
report=root/'reports'/('long-dot-'+stamp)
(report/'inputs').mkdir(parents=True);(report/'workload').mkdir()
sources=[root/'examples/long_dot_kernel.c',*(root/'workloads'/p for p in ('start.S','link.ld','console.h'))]
for p in sources:shutil.copy2(p,report/'inputs'/p.name)
shutil.copy2(args.flash.resolve(strict=True),report/'workload/flash.bin')
commands=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(argv,**kwargs):
    commands.append(list(map(str,argv)));(report/'commands.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2)+'\n')
    return subprocess.run(list(map(str,argv)),cwd=root,check=True,**kwargs)
elf=report/'workload/long-dot.elf';binary=elf.with_suffix('.bin')
with (report/'build.log').open('w') as log:
    run(['riscv64-unknown-elf-gcc','-march=rv64gcv','-mabi=lp64d','-mcmodel=medany','-O2',
         '-fno-tree-vectorize','-ffreestanding','-fno-builtin','-nostdlib','-nostartfiles',
         '-I'+str(report/'inputs'),'-Wl,--no-relax','-Wl,-T,'+str(report/'inputs/link.ld'),
         report/'inputs/start.S',report/'inputs/long_dot_kernel.c','-o',elf],stdout=log,stderr=log)
run(['riscv64-unknown-elf-objcopy','-O','binary',elf,binary])
with elf.with_suffix('.dis').open('w') as log:run(['riscv64-unknown-elf-objdump','-d',elf],stdout=log)
disassembly=elf.with_suffix('.dis').read_text();audits={}
for name in ('dot_four','rvv_reduce_four','rvv_lane_sixteen'):
    match=re.search(r'^[0-9a-f]+ <'+name+r'>:\n(.*?)(?=\n[0-9a-f]+ <|\Z)',disassembly,re.M|re.S);assert match,name
    instructions=[(int(m[1],16),int(m[2],16),m[3]) for m in re.finditer(r'^\s*([0-9a-f]+):\s+([0-9a-f]+)\s+(.+)$',match[1],re.M)]
    stores=[i for i in instructions if i[2].startswith('vs1r.v')];assert len(stores)==1
    if name=='dot_four':assert sum((i[1]&0xfc00707f)==0x0000000b for i in instructions)==4
    elif name=='rvv_reduce_four':assert sum(i[2].startswith('vwredsum.vs') for i in instructions)==4
    else:assert sum(i[2].startswith('vwadd.wv') for i in instructions)==2 and sum(i[2].startswith('vredsum.vs') for i in instructions)==1
    begin=next(i for i,instruction in enumerate(instructions) if instruction[2].startswith('vle8.v'))
    end=next(i for i in range(begin,len(instructions)) if instructions[i][2].startswith('bnez'))
    loop=instructions[begin:end+1]
    output_register=re.search(r'\((\w+)\)',stores[0][2])[1]
    changed_registers={m[1] for instruction in loop if (m:=re.match(r'addi\s+(\w+),',instruction[2]))}
    assert output_register not in changed_registers
    audits[name]={'single_final_vector_store':True,'final_store_pc':hex(stores[0][0]),'output_address_register':output_register,'loop_modified_gprs':sorted(changed_registers),'output_address_does_not_alias_modified_gprs':True,'asm_constraints':'three +&r early-clobber read-write GPRs','loop_instruction_count':len(loop),'operation':'four independent eight-item dots' if name=='dot_four' else 'four widening reductions seeded by old accumulators' if name=='rvv_reduce_four' else 'sixteen active int8 lanes and int32 lane accumulation followed by final reduction'}
(report/'assembly-audit.json').write_text(json.dumps(audits,ensure_ascii=False,indent=2)+'\n')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
input_sha={str(p):sha(p) for p in [args.emu.resolve(strict=True),args.reference.resolve(strict=True),binary,report/'workload/flash.bin',*sorted((report/'inputs').iterdir())]}
(report/'artifacts.json').write_text(json.dumps(input_sha,ensure_ascii=False,indent=2)+'\n')
(report/'source.json').write_text(json.dumps({'project_head':head,'working_tree_required_clean':False,'snapshot_source_sha256':{str(p):sha(p) for p in sources},'runner_sha256':sha(Path(__file__))},ensure_ascii=False,indent=2)+'\n')
print('LONG_DOT_PREPARED '+str(report),flush=True)
if args.build_only:raise SystemExit(0)
command=[str(args.emu.resolve()),'-i',str(binary),'-F',str(report/'workload/flash.bin'),'--ram-size=128MB','--diff='+str(args.reference.resolve()),'--no-squash','-C','4000000']
commands.append(command);(report/'commands.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2)+'\n')
with (report/'run.log').open('w') as log:
    r=subprocess.run(['systemd-run','--user','--scope','--unit=vdot-long-dot-'+stamp,'-p','MemoryMax=2500M','-p','MemorySwapMax=0','/usr/bin/time','-v','-o',str(report/'time.txt'),*command],cwd=root,stdout=log,stderr=log)
(report/'exit-status.txt').write_text(str(r.returncode)+'\n');assert r.returncode==0
text=re.sub(r'\x1b\[[0-9;]*m','',(report/'run.log').read_text())
assert 'LONG_DOT_PASS samples=45' in text and 'LONG_DOT_DIRECTED_PASS cases=12 lengths=2 variants=3' in text
assert 'Difftest enabled.' in text and 'HIT GOOD TRAP' in text and 'dirty: 0' in text
assert not re.search(r'ABORT|different at pc|HIT BAD TRAP|CRITICAL ERROR|mismatch',text,re.I)
def random_word(state):
    state^=(state<<13)&0xffffffff;state^=state>>17;state^=(state<<5)&0xffffffff;return state&0xffffffff
state=20261106;a=[];b=[]
for _ in range(512):
    state=random_word(state);x=state&255;a.append(x-256 if x>=128 else x)
    state=random_word(state);x=state&255;b.append(x-256 if x>=128 else x)
golden={k:sum(a[i]*b[i] for i in range(k)) for k in (32,128,512)}
matches=re.findall(r'^LONG_DOT,(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(-?\d+)$',text,re.M)
assert len(matches)==9
rows=[];summary=[]
for row in matches:
    variant,k,*values,result=map(int,row);assert variant in (0,1,2) and result==golden[k]
    assert len(values)==5 and min(values)>0
    rows.extend({'variant':variant,'k':k,'repeat':i,'cycles':v,'result':result} for i,v in enumerate(values))
    summary.append({'variant':variant,'k':k,'median_cycles':statistics.median(values),'min_cycles':min(values),'max_cycles':max(values),'result':result})
assert len({(r['variant'],r['k']) for r in summary})==9
directed=[]
for row in re.findall(r'^LONG_DIR,(\d+),(\d+),(-?\d+),(-?\d+),(-?\d+),(-?\d+)$',text,re.M):
    k,case,expected,*actual=map(int,row);assert k in (32,512) and case in (2,3)
    want=k*(-128)*(-128 if case==2 else 127)
    assert expected==want and actual==[want]*3
    directed.append({'k':k,'case':case,'expected':want,'actual':actual})
assert len(directed)==4 and len({(r['k'],r['case']) for r in directed})==4
comparisons=[]
for k in (32,128,512):
    by={r['variant']:r for r in summary if r['k']==k};baseline=min((1,2),key=lambda variant:by[variant]['median_cycles'])
    comparisons.append({'k':k,'vdot_median':by[0]['median_cycles'],'rvv_reduce_median':by[1]['median_cycles'],'rvv_lane_median':by[2]['median_cycles'],'selected_baseline_variant':baseline,'selected_baseline_median':by[baseline]['median_cycles'],'speedup':by[baseline]['median_cycles']/by[0]['median_cycles']})
assert all(sha(Path(p))==value for p,value in input_sha.items())
receipt={'status':'passed','directory':str(report),'project_head_at_preparation':head,'raw_exit_status':r.returncode,'difftest_enabled':True,'core_dirty':0,'wave_dump_enabled':False,'sample_count':len(rows),'repeats':5,'lengths':[32,128,512],'golden_results':golden,'directed_extremes_printed':directed,'directed_case_combinations':12,'directed_kernel_executions':36,'rows':rows,'summary':summary,'comparisons':comparisons,'emu':str(args.emu.resolve()),'reference':str(args.reference.resolve()),'input_sha256':input_sha,'run_log_sha256':sha(report/'run.log'),'measurement_boundary':'cycle/fence before initialization; includes necessary vector configurations, accumulator initialization, all input loads, loop control, cross-block accumulation, final combination/reduction, exactly one full 16-byte final result store and ending fence; C golden checks outside timing','variants':{'0':'vdot, eight-item blocks, four accumulators, four-way unroll','1':'RVV eight-item widening multiply/reduction, four int32 scalar-in-vector accumulators','2':'RVV sixteen-item widening multiply, two int32 lane accumulator groups, one final reduction'}}
(report/'results.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print('LONG_DOT_PASSED '+str(report),flush=True);print(json.dumps(comparisons,ensure_ascii=False),flush=True)
