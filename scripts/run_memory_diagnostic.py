"""Measure controlled vector-load register reuse and result-store variants."""
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

parser = argparse.ArgumentParser()
parser.add_argument('--emu', type=Path, required=True)
parser.add_argument('--reference', type=Path, required=True)
parser.add_argument('--flash', type=Path, required=True)
parser.add_argument('--blocks', type=int, default=128)
parser.add_argument('--repeats', type=int, default=3)
parser.add_argument('--require-clean', action='store_true')
parser.add_argument('--wave-begin', type=int)
parser.add_argument('--wave-end', type=int)
args = parser.parse_args()
assert args.blocks > 0 and args.blocks % 4 == 0 and args.repeats > 0
assert (args.wave_begin is None) == (args.wave_end is None)
if args.wave_begin is not None:
    assert 0 <= args.wave_begin < args.wave_end
root = Path(__file__).resolve().parents[1]
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip()
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + str(os.getpid())
report = root / 'reports' / ('memory-diagnostic-' + stamp)
(report / 'inputs').mkdir(parents=True)
(report / 'workload').mkdir()
for source in [root / 'examples/dot_memory_diagnostic.c',
               *(root / 'workloads' / s for s in ('start.S', 'link.ld', 'console.h'))]:
    shutil.copy2(source, report / 'inputs' / source.name)
shutil.copy2(args.flash.resolve(strict=True), report / 'workload/flash.bin')
commands = []


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def command(argv, **kwargs):
    commands.append([str(s) for s in argv])
    (report / 'commands.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2) + '\n')
    return subprocess.run([str(s) for s in argv], cwd=root, check=True, **kwargs)


command(['python3', root / 'scripts/source_manifest.py', report / 'source-before.json'],
        stdout=subprocess.DEVNULL)
elf = report / 'workload/memory-diagnostic.elf'
binary = elf.with_suffix('.bin')
with (report / 'build.log').open('w') as log:
    command(['riscv64-unknown-elf-gcc', '-march=rv64gcv', '-mabi=lp64d', '-mcmodel=medany',
             '-O2', '-fno-tree-vectorize', '-ffreestanding', '-fno-builtin', '-nostdlib', '-nostartfiles',
             '-DDIAG_BLOCKS=' + str(args.blocks), '-DDIAG_REPEATS=' + str(args.repeats),
             '-I' + str(report / 'inputs'), '-Wl,--no-relax',
             '-Wl,-T,' + str(report / 'inputs/link.ld'), report / 'inputs/start.S',
             report / 'inputs/dot_memory_diagnostic.c', '-o', elf], stdout=log, stderr=log)
command(['riscv64-unknown-elf-objcopy', '-O', 'binary', elf, binary])
with (elf.with_suffix('.dis')).open('w') as stream:
    command(['riscv64-unknown-elf-objdump', '-d', elf], stdout=stream)
disassembly = elf.with_suffix('.dis').read_text()
loops = {}
for match in re.finditer(r'^([0-9a-f]+) <((?:fixed|rotate)_(?:ta|tu)_(?:8|16))>:\n(.*?)(?=\n[0-9a-f]+ <|\Z)',
                         disassembly, re.M | re.S):
    name = match[2]
    instructions = [(int(m[1], 16), int(m[2], 16), m[3]) for m in
                    re.finditer(r'^\s*([0-9a-f]+):\s+([0-9a-f]+)\s+(.+)$', match[3], re.M)]
    first = next(i for i, instruction in enumerate(instructions) if instruction[2].startswith('vle8.v'))
    last = next(i for i in range(first, len(instructions)) if instructions[i][2].startswith('bnez'))
    loop = instructions[first:last + 1]
    branch_target = int(re.search(r'bnez\s+\w+,\s*([0-9a-f]+)', loop[-1][2])[1], 16)
    assert branch_target == loop[0][0]
    loads = [instruction for instruction in loop if instruction[2].startswith('vle8.v')]
    dots = [instruction for instruction in loop if instruction[1] & 0xfc00707f == 0x0000000b]
    stores = [instruction for instruction in loop if instruction[2].startswith(('vs1r.v', 'vse8.v'))]
    assert (len(loop), len(loads), len(dots), len(stores)) == (30, 8, 4, 4)
    loops[name] = {'begin_pc': hex(loop[0][0]), 'branch_pc': hex(loop[-1][0]),
                   'instructions_per_four_blocks': len(loop), 'vector_loads': len(loads),
                   'dot_instructions': len(dots), 'vector_stores': len(stores)}
assert len(loops) == 8
(report / 'loop-audit.json').write_text(json.dumps(loops, indent=2) + '\n')
emu, reference = args.emu.resolve(strict=True), args.reference.resolve(strict=True)
inputs = {str(p): digest(p) for p in (emu, reference, binary, report / 'workload/flash.bin',
          report / 'inputs/dot_memory_diagnostic.c')}
(report / 'artifacts.json').write_text(json.dumps(inputs, ensure_ascii=False, indent=2) + '\n')
simulation = [emu, '-i', binary, '-F', report / 'workload/flash.bin', '--ram-size=128MB',
              '--diff=' + str(reference), '--no-squash', '-C', '4000000']
if args.wave_begin is not None:
    simulation += ['--dump-wave-full', '-b', str(args.wave_begin), '-e', str(args.wave_end),
                   '--wave-path=' + str(report / 'wave.fst')]
commands.append([str(s) for s in simulation])
(report / 'commands.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2) + '\n')
print('MEMORY_DIAGNOSTIC_STARTED ' + str(report), flush=True)
with (report / 'run.log').open('w') as log:
    result = subprocess.run(['systemd-run', '--user', '--scope', '--unit=vdot-memdiag-' + stamp,
                             '-p', 'MemoryMax=3G', '-p', 'MemorySwapMax=0', '/usr/bin/time', '-v',
                             '-o', str(report / 'time.txt'), *map(str, simulation)],
                            cwd=root, stdout=log, stderr=log)
(report / 'exit-status.txt').write_text(str(result.returncode) + '\n')
assert result.returncode == 0
text = re.sub(r'\x1b\[[0-9;]*m', '', (report / 'run.log').read_text())
assert 'Difftest enabled.' in text and 'HIT GOOD TRAP' in text and 'MEMORY_DIAGNOSTIC_PASS' in text
assert not re.search(r'ABORT|different at pc|HIT BAD TRAP|CRITICAL ERROR|mismatch', text, re.I)
version = re.search(r"Commit SHA is: ([0-9a-f]+), dirty: ([01])", text)
assert version is not None
if args.require_clean:
    assert version[2] == '0'
rows = [tuple(map(int, m)) for m in re.findall(r'^MEMDIAG,(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)$', text, re.M)]
assert len(rows) == 8 * args.repeats
assert len({row[:5] for row in rows}) == len(rows) and len({row[-1] for row in rows}) == 1
summary = []
for tu in (0, 1):
    for rotating in (0, 1):
        for store in (16, 8):
            chosen = [r for r in rows if r[:4] == (tu, rotating, store, args.blocks)]
            assert sorted(r[4] for r in chosen) == list(range(args.repeats))
            values = [r[5] for r in chosen]
            assert min(values) > 0
            summary.append({'tail_undisturbed': tu, 'rotating': rotating, 'store_bytes': store,
                            'blocks': args.blocks, 'cycles_median': statistics.median(values),
                            'cycles_min': min(values), 'cycles_max': max(values)})
command(['python3', root / 'scripts/source_manifest.py', report / 'source-after.json'],
        stdout=subprocess.DEVNULL)
before = json.loads((report / 'source-before.json').read_text())
after = json.loads((report / 'source-after.json').read_text())
for field in ('project_head', 'repositories', 'project_files_sha256'):
    assert before[field] == after[field]
assert all(digest(Path(p)) == value for p, value in inputs.items())
receipt = {'status': 'passed', 'source_project_head': before['project_head'], 'source_unchanged': True,
           'emu': str(emu), 'emu_sha256': inputs[str(emu)], 'reported_core_commit_prefix': version[1],
           'reported_core_dirty': int(version[2]), 'difftest_enabled': True, 'raw_exit_status': 0,
           'wave_dump_enabled': args.wave_begin is not None, 'sample_count': len(rows),
           'rows': rows, 'summary': summary, 'checksum': rows[0][-1],
           'run_log_sha256': digest(report / 'run.log'),
           'boundary': 'four-way unrolled loop, two 8-byte vector loads and one result store per block; common full-output zeroing outside timing; all 128-bit memory results checked',
           'purpose': 'controlled diagnostic; complements the unchanged full-layout RVV/vdot benchmark'}
(report / 'results.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
print('MEMORY_DIAGNOSTIC_PASSED ' + str(report), flush=True)
print(json.dumps(summary, ensure_ascii=False), flush=True)
