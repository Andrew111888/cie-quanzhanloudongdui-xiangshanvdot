"""Require normal, erroneous and restored references to produce expected outcomes."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,re,shutil,subprocess
parser=argparse.ArgumentParser();parser.add_argument('--emu',type=Path,required=True);parser.add_argument('--reference',type=Path,required=True);parser.add_argument('--bad-reference',type=Path,required=True);parser.add_argument('--flash',type=Path,required=True);args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');out=root/'reports'/('acc-fault-check-'+stamp);(out/'inputs').mkdir(parents=True);(out/'workload').mkdir()
for name in ('examples/acc_probe.c','scripts/run_acc_fault_check.py','workloads/start.S','workloads/console.h','workloads/link.ld'):shutil.copy2(root/name,out/'inputs'/Path(name).name)
elf=out/'workload/acc-probe.elf';binary=elf.with_suffix('.bin');emu=args.emu.resolve(strict=True);good=args.reference.resolve(strict=True);flash=args.flash.resolve(strict=True)
bad=args.bad_reference.resolve(strict=True)
with (out/'build.log').open('w') as log:
 subprocess.run(['riscv64-unknown-elf-gcc','-march=rv64gcv','-mabi=lp64d','-mcmodel=medany','-O2','-fno-tree-vectorize','-ffreestanding','-fno-builtin','-nostdlib','-nostartfiles','-I'+str(out/'inputs'),'-Wl,--no-relax','-Wl,-T,'+str(out/'inputs/link.ld'),out/'inputs/start.S',out/'inputs/acc_probe.c','-o',elf],check=True,stdout=log,stderr=log)
 subprocess.run(['riscv64-unknown-elf-objcopy','-O','binary',elf,binary],check=True)
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();bound={str(p.resolve()):h(p) for p in [emu,good,bad,flash,binary,*sorted((out/'inputs').iterdir())]};runs=[]
for label,ref,expected in [('normal',good,0),('injected',bad,1),('restored',good,0)]:
 cmd=[str(emu),'-i',str(binary),'-F',str(flash),'--ram-size=128MB','--diff='+str(ref),'--no-squash','-C','100000']
 with (out/(label+'.log')).open('w') as log:r=subprocess.run(cmd,cwd=root,stdout=log,stderr=log)
 (out/(label+'-exit-status.txt')).write_text(str(r.returncode)+'\n');assert r.returncode==expected,(label,r.returncode)
 text=(out/(label+'.log')).read_text();assert 'Difftest enabled.' in text and 'dirty: 0' in text
 if expected:
  assert 'different at pc' in text and 'v12_low' in text and 'ABORT' in text and '0x0000000012345681' in text and '0x0000000012345680' in text
  commit=re.search(r'^\[\d+\] commit pc ([0-9a-f]{16}) inst 06a4060b wen 1 dst 12 data [0-9a-f]{16} idx [0-9a-f]{3}([^\r\n]*)',text,re.M)
  assert commit and not re.search(r'\([SDW]\)',commit[2])
 else:assert 'HIT GOOD TRAP' in text and 'ACC_PROBE_PASS' in text
 runs.append({'label':label,'exit_status':r.returncode,'command':cmd,'log_sha256':h(out/(label+'.log'))})
for p,value in bound.items():assert h(Path(p))==value
(out/'results.json').write_text(json.dumps({'status':'passed','scope':'real_rtl_nemu_acc_fault_and_restore','input_sha256':bound,'runs':runs,'injected_result_low_bit_mismatch':'12345681 / 12345680','normal_and_restored_results':'12345680 with zero high96'},indent=2)+'\n')
print('ACC_FAULT_AND_RESTORE_PASSED '+str(out),flush=True)
