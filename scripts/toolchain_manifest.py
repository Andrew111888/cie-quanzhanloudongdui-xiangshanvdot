"""Record the actual local binaries used by this pinned build workflow."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

parser=argparse.ArgumentParser()
parser.add_argument('output',type=Path)
parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
args=parser.parse_args()
root=args.root.resolve(strict=True)
java_home=os.environ.get('JAVA_HOME')
if not java_home:raise SystemExit('Source scripts/env.sh before collecting the toolchain')
verilator=os.environ.get('VDOT_VERILATOR_BIN','/home/yh/chipyard/.conda-env/bin/verilator_bin')
firtool=os.environ.get('VDOT_FIRTOOL',str(Path.home()/'.cache/llvm-firtool/1.62.1/bin/firtool'))
items={'java':(str(Path(java_home)/'bin/java'),['-version']),
       'verilator':(verilator,['--version']), 'firtool':(firtool,['--version']),
       'riscv-gcc':(shutil.which('riscv64-unknown-elf-gcc'),['--version']),
       'host-gcc':(os.environ.get('VDOT_HOST_CC','/usr/bin/gcc'),['--version']),
       'host-g++':(os.environ.get('VDOT_HOST_CXX','/usr/bin/g++'),['--version']),
       'make':(shutil.which('make'),['--version']), 'python':(sys.executable,['--version']),
       'fst2vcd':(shutil.which('fst2vcd'),['--help'])}
result={'recorded_at_utc':datetime.now(timezone.utc).isoformat(), 'build_root':str(root), 'tools':{}}
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
for name,(binary,flags) in items.items():
 if not binary:raise SystemExit('Missing tool '+name)
 path=Path(binary).resolve(strict=True)
 command=subprocess.run([str(path),*flags],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 result['tools'][name]={'path':str(path),'sha256':digest(path),
                       'version_command_exit':command.returncode,
                       'version_output':'\n'.join(command.stdout.splitlines()[:8])}
for name,path in {'mill-artifact':root/'tools/mill',
                  'verilator-trace-compatibility':root/'configs/verilator_5_022_trace.h',
                  'libvmmalloc':root/'tools/sysroot/usr/lib/x86_64-linux-gnu/libvmmalloc.so.1'}.items():
 path=path.resolve(strict=True);result['tools'][name]={'path':str(path),'sha256':digest(path)}
result['mill_version']=(root/'.mill-version').read_text().strip()
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(result,indent=2)+'\n')
print('TOOLCHAIN_IDENTITY_RECORDED',args.output)
