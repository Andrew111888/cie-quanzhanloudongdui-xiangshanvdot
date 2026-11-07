"""Trace the existing isolation test while preserving its original checks."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--verilator', default='/home/yh/chipyard/.conda-env/bin/verilator')
args = parser.parse_args()
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out = root / 'reports' / f'isolation-wave-{stamp}-{os.getpid()}'
sources = out / 'sources'
sources.mkdir(parents=True)
files = ['rtl/VdotAccRetimedDatapath.sv', 'experiments/isolation/IsolationCompare.sv',
         'experiments/isolation/isolation_test.cpp']
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
bindings = {}
for name in files:
    shutil.copyfile(root / name, sources / Path(name).name)
    bindings[name] = sha(root / name)
text = (sources / 'isolation_test.cpp').read_text()
replacements = {
    '#include "verilated.h"': '#include "verilated.h"\n#include "verilated_vcd_c.h"',
    'Verilated::commandArgs(argc,argv);': 'Verilated::commandArgs(argc,argv);\n Verilated::traceEverOn(true);\n require(argc==2,"trace output path required");',
    'VIsolationCompare d;': 'VIsolationCompare d;\n  VerilatedVcdC trace;\n  if(mode==1){d.trace(&trace,99);trace.open(argv[1]);}',
    '    d.eval();sample();': '    d.eval();sample();\n    if(mode==1 && cycle>=960 && cycle<=1020)trace.dump(cycle*2+1);',
    '    d.clock=1;d.eval();sample();': '    d.clock=1;d.eval();sample();\n    if(mode==1 && cycle>=960 && cycle<=1020)trace.dump(cycle*2+2);',
    '  d.final();': '  d.final();\n  if(mode==1)trace.close();',
}
for before, after in replacements.items():
    assert text.count(before) == 1, before
    text = text.replace(before, after)
harness = sources / 'trace_test.cpp'
harness.write_text(text)
obj = out / 'obj_dir'
commands = [[args.verilator, '--cc', '--exe', '--build', '--trace', '--top-module',
             'IsolationCompare', '-DSYNTHESIS', '-Wno-fatal', '--Mdir', str(obj), '-j', '2',
             '-CFLAGS', '-std=c++17 -O2', '-MAKEFLAGS', 'CXX=/usr/bin/g++ LINK=/usr/bin/g++',
             str(sources / 'VdotAccRetimedDatapath.sv'), str(sources / 'IsolationCompare.sv'), str(harness)],
            [str(obj / 'VIsolationCompare'), str(out / 'wave.vcd')]]
for command, name in zip(commands, ['build.log', 'run.log']):
    with (out / name).open('w') as stream:
        subprocess.run(command, cwd=root, stdout=stream, stderr=subprocess.STDOUT, check=True)
log = (out / 'run.log').read_text()
assert log.count('ISOLATION_PASS ') == 4 and 'ISOLATION_FAIL' not in log
for name, digest in bindings.items():
    assert sha(root / name) == digest
record = {'status': 'passed', 'scope': 'isolated_wrapper_vcd', 'source_sha256': bindings,
          'trace_harness_sha256': sha(harness), 'trace_only_additions': True,
          'full_original_scoreboard_checks_enabled': True, 'mode': 1,
          'cycle_window': [960, 1020], 'vcd_sha256': sha(out / 'wave.vcd'),
          'run_log_sha256': sha(out / 'run.log'), 'commands': commands}
(out / 'results.json').write_text(json.dumps(record, indent=2)+'\n')
print(out)
