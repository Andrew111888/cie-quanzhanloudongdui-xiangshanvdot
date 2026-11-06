"""Build and measure fused-accumulate versus explicit-add and RVV kernels."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--emu', type=Path)
parser.add_argument('--reference', type=Path)
parser.add_argument('--flash', type=Path, help='Use this fixed flash; otherwise build the pinned flash.S')
parser.add_argument('--build-receipt', type=Path, help='Optional source/build receipt for the supplied emulator')
parser.add_argument('--tool-prefix', default='riscv64-unknown-elf-')
parser.add_argument('--build-only', action='store_true')
parser.add_argument('--allow-dirty-core', action='store_true')
parser.add_argument('--cycle-limit', type=int, default=12000000)
parser.add_argument('--output', type=Path)
args = parser.parse_args()
if not args.build_only and (args.emu is None or args.reference is None):
    parser.error('--emu and --reference are required unless --build-only is selected')
if args.cycle_limit <= 0:
    parser.error('--cycle-limit must be positive')
root = Path(__file__).resolve().parents[1]
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + str(os.getpid())
report = (args.output or root / 'reports' / ('acc-benchmark-' + stamp)).resolve()
(report / 'inputs').mkdir(parents=True, exist_ok=False)
(report / 'workload').mkdir()
commands = []


def run(argv, **kwargs):
    record = {'argv': list(map(str, argv)), 'cwd': str(root)}
    commands.append(record)
    write_json(report / 'commands.json', commands)
    result = subprocess.run(record['argv'], cwd=root, **kwargs)
    record['exit_status'] = result.returncode
    write_json(report / 'commands.json', commands)
    result.check_returncode()
    return result


toolchain = {}
for suffix in ('gcc', 'objcopy', 'objdump'):
    found = shutil.which(args.tool_prefix + suffix)
    if found is None:
        raise SystemExit('Missing cross tool: ' + args.tool_prefix + suffix)
    tool = Path(found).resolve(strict=True)
    version = run([tool, '--version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout
    toolchain[suffix] = {'path': str(tool), 'sha256': digest(tool), 'version': version.strip()}
write_json(report / 'toolchain.json', toolchain)
sources = [root / 'examples/acc_benchmark.c',
           *(root / 'workloads' / name for name in ('start.S', 'link.ld', 'console.h', 'flash.S'))]
source_hashes = {str(path): digest(path) for path in sources}
for path in sources:
    shutil.copy2(path, report / 'inputs' / path.name)
shutil.copy2(Path(__file__), report / 'inputs/run_acc_benchmark.py')
source_hashes[str(Path(__file__))] = digest(Path(__file__))
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
write_json(report / 'source.json', {'project_head_at_preparation': head,
                                  'working_tree_required_clean': False,
                                  'snapshot_source_sha256': source_hashes,
                                  'scope': 'New experimental workload snapshot; no old emulator run is implied'})
elf = report / 'workload/acc-benchmark.elf'
binary = elf.with_suffix('.bin')
with (report / 'build.log').open('w') as log:
    run([toolchain['gcc']['path'], '-march=rv64gcv', '-mabi=lp64d', '-mcmodel=medany', '-O2',
         '-fno-tree-vectorize', '-ffreestanding', '-fno-builtin', '-nostdlib', '-nostartfiles',
         '-I' + str(report / 'inputs'), '-Wl,--no-relax', '-Wl,-T,' + str(report / 'inputs/link.ld'),
         report / 'inputs/start.S', report / 'inputs/acc_benchmark.c', '-o', elf], stdout=log, stderr=log)
    if args.flash:
        shutil.copy2(args.flash.resolve(strict=True), report / 'workload/flash.bin')
    else:
        flash_elf = report / 'workload/flash.elf'
        run([toolchain['gcc']['path'], '-march=rv64gc', '-mabi=lp64d', '-nostdlib', '-nostartfiles',
             '-Wl,-Ttext=0x10000000', report / 'inputs/flash.S', '-o', flash_elf], stdout=log, stderr=log)
        run([toolchain['objcopy']['path'], '-O', 'binary', flash_elf, report / 'workload/flash.bin'],
            stdout=log, stderr=log)
run([toolchain['objcopy']['path'], '-O', 'binary', elf, binary])
with elf.with_suffix('.dis').open('w') as stream:
    run([toolchain['objdump']['path'], '-d', elf], stdout=stream)
disassembly = elf.with_suffix('.dis').read_text()


def instructions(name):
    match = re.search(r'^[0-9a-f]+ <' + re.escape(name) + r'>:\n(.*?)(?=\n[0-9a-f]+ <|\Z)',
                      disassembly, re.M | re.S)
    assert match, name
    return [(int(m[1], 16), int(m[2], 16), m[3]) for m in
            re.finditer(r'^\s*([0-9a-f]+):\s+([0-9a-f]+)\s+(.+)$', match[1], re.M)]


def written_gpr(instruction):
    bits = instruction[1]
    if bits & 3 == 3:
        opcode = bits & 0x7f
        if opcode in (0x03, 0x13, 0x17, 0x1b, 0x33, 0x37, 0x3b, 0x67, 0x6f, 0x73):
            return (bits >> 7) & 31
        if opcode == 0x57 and (bits >> 12) & 7 == 7:  # vset* writes an integer destination.
            return (bits >> 7) & 31
        return 0
    quadrant, function = bits & 3, (bits >> 13) & 7
    if quadrant == 1 and function in (0, 1, 2, 3):
        return (bits >> 7) & 31
    if quadrant == 2 and function in (0, 2, 3, 4):
        return (bits >> 7) & 31
    if quadrant == 0 and function in (0, 2, 3):
        return 8 + ((bits >> 2) & 7)
    return 0


abi = ['zero', 'ra', 'sp', 'gp', 'tp', 't0', 't1', 't2', 's0', 's1',
       'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 's2', 's3', 's4',
       's5', 's6', 's7', 's8', 's9', 's10', 's11', 't3', 't4', 't5', 't6']


def audit_loop(items, begin, expected_length, store_count):
    end = next(index for index in range(begin, len(items)) if items[index][2].startswith('bnez'))
    loop = items[begin:end + 1]
    target = int(re.search(r'bnez\s+\w+,\s*([0-9a-f]+)', loop[-1][2])[1], 16)
    assert target == loop[0][0] and len(loop) == expected_length
    stores = [item for item in items if item[2].startswith('vs1r.v')]
    assert len(stores) == store_count and all(item[0] > loop[-1][0] for item in stores)
    output_gpr = re.search(r'\((\w+)\)', stores[0][2])[1]
    output_number = int(output_gpr[1:]) if re.fullmatch(r'x\d+', output_gpr) else abi.index(output_gpr)
    changed = sorted({written_gpr(item) for item in loop} - {0})
    assert output_number not in changed
    counters = [item for item in items if re.search(r'\brdcycle\b', item[2])]
    assert len(counters) == 2 and counters[0][0] < loop[0][0] < stores[-1][0] < counters[1][0]
    return {'loop_begin_pc': hex(loop[0][0]), 'branch_pc': hex(loop[-1][0]),
            'loop_instruction_count': len(loop), 'output_address_register': output_gpr,
            'loop_modified_gprs': [abi[number] for number in changed],
            'output_address_does_not_alias_modified_gprs': True,
            'stores_after_loop_inside_timing': len(stores),
            'timed_begin_cycle_pc': hex(counters[0][0]), 'timed_end_cycle_pc': hex(counters[1][0])}, loop


audits = {}
for name, count in (('dot_four', 28), ('rvv_reduce_four', 28), ('rvv_lane_sixteen', 16), ('acc_four', 22)):
    items = instructions(name)
    begin = next(i for i, item in enumerate(items) if item[2].startswith('vle8.v'))
    audit, loop = audit_loop(items, begin, count, 1)
    audit['source_gpr_constraints'] = 'three +&r early-clobber read-write operands'
    if name == 'dot_four':
        assert sum((item[1] & 0xfc00707f) == 0x0000000b for item in loop) == 4
    elif name == 'acc_four':
        assert sum((item[1] & 0xfc00707f) == 0x0400000b for item in loop) == 4
    elif name == 'rvv_reduce_four':
        assert sum(item[2].startswith('vwredsum.vs') for item in loop) == 4
    else:
        assert sum(item[2].startswith('vwadd.wv') for item in loop) == 2
        assert sum(item[2].startswith('vredsum.vs') for item in items) == 1
    audits[name] = audit
for chains in (1, 2, 4, 8):
    for fused in (False, True):
        name = ('acc_chain_' if fused else 'dot_add_') + str(chains)
        items = instructions(name)
        begin = next(i for i, item in enumerate(items) if (item[1] & 0xfc00707f) in (0x0000000b, 0x0400000b))
        audit, loop = audit_loop(items, begin, chains + 2 if fused else 2 * chains + 4, chains)
        opcode = 0x0400000b if fused else 0x0000000b
        assert sum((item[1] & 0xfc00707f) == opcode for item in loop) == chains
        audit.update(chains=chains, fused=fused, source_gpr_constraints='one +&r loop counter; late output pointer is distinct')
        audits[name] = audit
write_json(report / 'assembly-audit.json', audits)

artifacts = {str(path): digest(path) for path in sorted((report / 'inputs').iterdir())}
artifacts.update({str(path): digest(path) for path in (elf, binary, elf.with_suffix('.dis'), report / 'workload/flash.bin')})
if args.build_receipt:
    receipt = args.build_receipt.resolve(strict=True)
    artifacts[str(receipt)] = digest(receipt)
if args.emu:
    artifacts[str(args.emu.resolve(strict=True))] = digest(args.emu.resolve())
if args.reference:
    artifacts[str(args.reference.resolve(strict=True))] = digest(args.reference.resolve())
write_json(report / 'artifacts.json', artifacts)
write_json(report / 'preparation.json', {'status': 'built_and_audited_not_simulated',
                                       'project_head': head, 'source_sha256': source_hashes,
                                       'instruction': {'mask': '0xfc00707f', 'match': '0x0400000b',
                                                       'semantic': 'old.low32 + signed int8 dot8 modulo 2^32; high96 zero'},
                                       'long_samples_expected': 60, 'chain_samples_expected': 120})
print('ACC_BENCHMARK_PREPARED ' + str(report), flush=True)
if args.build_only:
    raise SystemExit(0)
simulation = [str(args.emu.resolve()), '-i', str(binary), '-F', str(report / 'workload/flash.bin'),
              '--ram-size=128MB', '--diff=' + str(args.reference.resolve()), '--no-squash',
              '-C', str(args.cycle_limit)]
commands.append({'argv': simulation, 'cwd': str(root), 'wave_dump_enabled': False})
write_json(report / 'commands.json', commands)
with (report / 'run.log').open('w') as stream:
    completed = subprocess.run(['systemd-run', '--user', '--scope', '--unit=acc-bench-' + stamp,
                                '-p', 'MemoryMax=2500M', '-p', 'MemorySwapMax=0', '/usr/bin/time', '-v',
                                '-o', str(report / 'time.txt'), *simulation], cwd=root, stdout=stream, stderr=stream)
(report / 'exit-status.txt').write_text(str(completed.returncode) + '\n')
assert completed.returncode == 0
text = re.sub(r'\x1b\[[0-9;]*m', '', (report / 'run.log').read_text())
assert 'Difftest enabled.' in text and 'HIT GOOD TRAP' in text
assert 'ACC_BENCH_PASS long_samples=60 chain_samples=120 full_128bit_results=1' in text
assert 'ACC_LONG_DIRECTED_PASS cases=12 variants=4 executions=48' in text
assert 'ACC_CHAIN_DIRECTED_PASS cases=6 chain_counts=4 variants=2 executions=48' in text
assert not re.search(r'ABORT|different at pc|HIT BAD TRAP|CRITICAL ERROR|mismatch', text, re.I)
version = re.search(r'Commit SHA is: ([0-9a-f]+), dirty: ([01])', text)
assert version is not None
if not args.allow_dirty_core:
    assert version[2] == '0', 'Dirty experimental core must be explicitly allowed and recorded'


def random_word(state):
    state ^= (state << 13) & 0xffffffff
    state ^= state >> 17
    state ^= (state << 5) & 0xffffffff
    return state & 0xffffffff


state = 20261106
a, b = [], []
for _ in range(512):
    state = random_word(state); value = state & 255; a.append(value - 256 if value >= 128 else value)
    state = random_word(state); value = state & 255; b.append(value - 256 if value >= 128 else value)
golden = {k: sum(a[i] * b[i] for i in range(k)) for k in (8, 32, 128, 512)}
long_rows, long_summary = [], []
for row in re.findall(r'^ACC_LONG,(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(-?\d+)$', text, re.M):
    variant, k, *values, result = map(int, row)
    assert variant in range(4) and k in (32, 128, 512) and result == golden[k] and min(values) > 0
    long_rows.extend({'variant': variant, 'k': k, 'repeat': i, 'cycles': value, 'result': result}
                     for i, value in enumerate(values))
    long_summary.append({'variant': variant, 'k': k, 'median_cycles': statistics.median(values),
                         'min_cycles': min(values), 'max_cycles': max(values), 'result': result})
assert len(long_rows) == 60 and len({(r['variant'], r['k']) for r in long_summary}) == 12
long_directed = []
edges = ((1, 1), (-1, 1), (-128, -128), (-128, 127), (127, 127), (0, -128))
for row in re.findall(r'^ACC_LONG_DIR,(\d+),(\d+),(-?\d+),(-?\d+),(-?\d+),(-?\d+),(-?\d+)$', text, re.M):
    k, case, expected, *actual = map(int, row)
    assert k in (32, 512) and case in range(6)
    want = k * edges[case][0] * edges[case][1]
    assert expected == want and actual == [want] * 4
    long_directed.append({'k': k, 'case': case, 'expected': want, 'actual': actual})
assert len(long_directed) == 12 and len({(r['k'], r['case']) for r in long_directed}) == 12
chain_rows, chain_summary = [], []
for row in re.findall(r'^ACC_CHAIN,(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)$', text, re.M):
    variant, chains, rounds, *values = map(int, row)
    assert variant in (0, 1) and chains in (1, 2, 4, 8) and rounds in (32, 128, 512) and min(values) > 0
    operations = chains * rounds
    chain_rows.extend({'variant': variant, 'chains': chains, 'rounds': rounds, 'dot_operations': operations,
                      'repeat': i, 'cycles': value} for i, value in enumerate(values))
    median = statistics.median(values)
    chain_summary.append({'variant': variant, 'chains': chains, 'rounds': rounds, 'dot_operations': operations,
                          'median_cycles': median, 'min_cycles': min(values), 'max_cycles': max(values),
                          'median_fragment_cycles_per_dot': median / operations})
assert len(chain_rows) == 120 and len({(r['variant'], r['chains'], r['rounds']) for r in chain_summary}) == 24
chain_results = []
for row in re.findall(r'^ACC_CHAIN_RESULT,(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)$', text, re.M):
    variant, chains, rounds, index, *actual = map(int, row)
    assert variant in (0, 1) and chains in (1, 2, 4, 8) and rounds in (32, 128, 512) and index in range(chains)
    expected = (0x7ffffff0 + index * 0x10203 + rounds * golden[8]) & 0xffffffff
    assert actual == [expected, 0, 0, 0]
    chain_results.append({'variant': variant, 'chains': chains, 'rounds': rounds, 'index': index, 'words32': actual})
assert len(chain_results) == 90 and len({(r['variant'], r['chains'], r['rounds'], r['index']) for r in chain_results}) == 90
directed_chains = []
for row in re.findall(r'^ACC_CHAIN_DIR,(\d+),(\d+),(\d+),(\d+)$', text, re.M):
    case, variant, chains, actual = map(int, row)
    assert case in range(6) and variant in (0, 1) and chains in (1, 2, 4, 8)
    dot = 8 * edges[case][0] * edges[case][1]
    seed = 0x80000000 if dot < 0 else 0x7ffffff0
    expected = 0
    for index in range(chains):
        expected ^= (seed + index * 0x10203 + 32 * dot) & 0xffffffff
    assert actual == expected
    directed_chains.append({'case': case, 'variant': variant, 'chains': chains, 'checksum': actual})
assert len(directed_chains) == 48 and len({(r['case'], r['variant'], r['chains']) for r in directed_chains}) == 48
comparisons = []
for k in (32, 128, 512):
    by = {r['variant']: r for r in long_summary if r['k'] == k}
    selected = min((1, 2), key=lambda variant: by[variant]['median_cycles'])
    comparisons.append({'k': k, 'old_vdot_median': by[0]['median_cycles'], 'rvv8_median': by[1]['median_cycles'],
                        'rvv16_median': by[2]['median_cycles'], 'acc_median': by[3]['median_cycles'],
                        'selected_rvv_variant': selected, 'selected_rvv_median': by[selected]['median_cycles'],
                        'rvv_over_acc': by[selected]['median_cycles'] / by[3]['median_cycles'],
                        'old_vdot_over_acc': by[0]['median_cycles'] / by[3]['median_cycles']})
chain_comparisons = []
for chains in (1, 2, 4, 8):
    for rounds in (32, 128, 512):
        by = {r['variant']: r for r in chain_summary if r['chains'] == chains and r['rounds'] == rounds}
        chain_comparisons.append({'chains': chains, 'rounds': rounds,
                                  'dot_plus_add_median': by[0]['median_cycles'],
                                  'acc_median': by[1]['median_cycles'],
                                  'dot_plus_add_over_acc': by[0]['median_cycles'] / by[1]['median_cycles']})
for path, value in artifacts.items():
    assert digest(Path(path)) == value, path
for path, value in source_hashes.items():
    assert digest(Path(path)) == value, path
for name, rows in (('long-samples.csv', long_rows), ('long-summary.csv', long_summary),
                   ('chain-samples.csv', chain_rows), ('chain-summary.csv', chain_summary),
                   ('long-comparisons.csv', comparisons), ('chain-comparisons.csv', chain_comparisons)):
    with (report / name).open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
write_json(report / 'results.json', {
    'status': 'passed', 'directory': str(report), 'raw_exit_status': completed.returncode,
    'project_head_at_preparation': head,
    'project_head_at_completion': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
    'selected_inputs_unchanged': True, 'difftest_enabled': True,
    'reported_core_commit_prefix': version[1], 'reported_core_dirty': int(version[2]),
    'dirty_core_explicitly_allowed': args.allow_dirty_core, 'wave_dump_enabled': False,
    'golden_results': golden, 'long_sample_count': len(long_rows), 'chain_sample_count': len(chain_rows),
    'repeats': 5, 'lengths': [32, 128, 512], 'independent_chain_counts': [1, 2, 4, 8],
    'long_directed': long_directed, 'chain_directed': directed_chains, 'full_chain_results': chain_results,
    'long_rows': long_rows, 'long_summary': long_summary, 'long_comparisons': comparisons,
    'chain_rows': chain_rows, 'chain_summary': chain_summary, 'chain_comparisons': chain_comparisons,
    'input_sha256': artifacts, 'run_log_sha256': digest(report / 'run.log'),
    'long_boundary': 'cycle/fence before vector initialization; configurations, loads, loop, accumulation, final combine/reduction, one full 16-byte store and ending fence; output sentinel and scalar golden checks outside',
    'chain_boundary': 'sources and all eight seeds preloaded before cycle/fence; time loop, necessary per-round configurations, branch and complete final 16-byte stores for active chains; seeds, sentinel and scalar golden checks outside; this is not bare FU latency',
    'long_variants': {'0': 'vdot plus explicit four-accumulator vadd', '1': 'RVV8 widening reduction',
                      '2': 'RVV16 lane accumulation and final reduction', '3': 'vdot.acc four accumulators'},
    'chain_variants': {'0': 'vdot plus explicit e32 vadd', '1': 'vdot.acc'},
})
print('ACC_BENCHMARK_PASSED ' + str(report), flush=True)
print(json.dumps({'long_comparisons': comparisons, 'chain_comparisons': chain_comparisons}, ensure_ascii=False), flush=True)
