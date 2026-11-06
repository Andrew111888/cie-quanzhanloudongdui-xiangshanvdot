"""Check v0/v31 accumulating dot products and aliases on NEMU and/or RTL."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,re,shutil,subprocess
parser=argparse.ArgumentParser();parser.add_argument('--nemu',type=Path);parser.add_argument('--emu',type=Path);parser.add_argument('--reference',type=Path);parser.add_argument('--flash',type=Path,required=True);args=parser.parse_args()
assert args.nemu or args.emu
assert bool(args.emu)==bool(args.reference)
root=Path(__file__).resolve().parents[1];stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=root/'reports'/('acc-registers-'+stamp);(out/'inputs').mkdir(parents=True);(out/'workload').mkdir()
for n in ('examples/acc_registers.c','scripts/run_acc_registers.py','workloads/start.S','workloads/console.h','workloads/link.ld'):shutil.copy2(root/n,out/'inputs'/Path(n).name)
elf=out/'workload/acc-registers.elf';binary=elf.with_suffix('.bin');flash=args.flash.resolve(strict=True);h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with (out/'build.log').open('w') as log:
 subprocess.run(['riscv64-unknown-elf-gcc','-march=rv64gcv','-mabi=lp64d','-mcmodel=medany','-O2','-fno-tree-vectorize','-ffreestanding','-fno-builtin','-nostdlib','-nostartfiles','-I'+str(out/'inputs'),'-Wl,--no-relax','-Wl,-T,'+str(out/'inputs/link.ld'),out/'inputs/start.S',out/'inputs/acc_registers.c','-o',elf],check=True,stdout=log,stderr=log)
 subprocess.run(['riscv64-unknown-elf-objcopy','-O','binary',elf,binary],check=True)
commands=[];executables=[]
if args.nemu:
 nemu=args.nemu.resolve(strict=True);executables.append(nemu);commands.append(('nemu',[str(nemu),'--batch','--flash-image='+str(flash),str(binary)]))
if args.emu:
 emu=args.emu.resolve(strict=True);ref=args.reference.resolve(strict=True);executables.extend([emu,ref]);commands.append(('rtl',[str(emu),'-i',str(binary),'-F',str(flash),'--ram-size=128MB','--diff='+str(ref),'--no-squash','-C','200000']))
bound={str(p.resolve()):h(p) for p in [binary,flash,*sorted((out/'inputs').iterdir())]+executables};runs=[]
for label,cmd in commands:
 with (out/(label+'.log')).open('w') as stream:r=subprocess.run(cmd,cwd=root,stdout=stream,stderr=stream)
 (out/(label+'-exit-status.txt')).write_text(str(r.returncode)+'\n');assert r.returncode==0
 text=(out/(label+'.log')).read_text();assert 'ACC_REGISTERS_PASS' in text and 'HIT GOOD TRAP' in text
 if label=='rtl':assert 'dirty: 0' in text and 'Difftest enabled.' in text
 assert not re.search(r'ABORT|HIT BAD TRAP|different at pc|mismatch',text,re.I)
 runs.append({'label':label,'command':cmd,'log_sha256':h(out/(label+'.log'))})
for p,value in bound.items():assert h(Path(p))==value
(out/'results.json').write_text(json.dumps({'status':'passed','scope':'rtl_nemu_difftest' if args.emu else 'nemu_standalone','forms':6,'policies':2,'input_sha256':bound,'runs':runs},indent=2)+'\n');print('ACC_REGISTERS_PASSED '+str(out),flush=True)
