"""Prove a completed wrong-path vdot is flushed before architectural commit.

The optional bounded capture is diagnostic only. A separate completed pressure
run with identical emulator, REF, workload and flash is mandatory evidence.
"""
import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--events', type=Path, required=True)
parser.add_argument('--full-run', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
metadata = json.loads((args.events / 'metadata.json').read_text())
events = json.loads((args.events / 'events.json').read_text())
capture = Path(metadata['fst']).parent
if (args.full_run / 'exit-status.txt').read_text().strip() != '0':
    raise SystemExit('Completed pressure run did not exit zero')
if 'Difftest enabled.' not in (args.full_run / 'run.log').read_text():
    raise SystemExit('Missing real Difftest initialization')
subprocess.run([sys.executable, str(Path(__file__).with_name('check_run.py')),
                str(args.full_run / 'run.log'), 'PIPELINE_PASS bursts=64 vdot_instructions=1664'], check=True)


def hashes(directory):
    return {Path(name).name: digest for digest, name in
            (line.split(maxsplit=1) for line in (directory / 'artifacts.sha256').read_text().splitlines())}


if hashes(capture) != hashes(args.full_run):
    raise SystemExit('Diagnostic capture and completed run have different inputs')


def key(event):
    return event.get('rob_flag'), event.get('rob_value')


def one(items, label):
    if len(items) != 1:
        raise ValueError(f'{label}: expected one event, got {len(items)}')
    return items[0]


renames = [e for e in events if e['kind'] == 'rename']
commits = [e for e in events if e['kind'] == 'commit']
redirects = [e for e in events if e['kind'] == 'redirect']
inputs = [e for e in events if e['kind'] == 'fu_in' and e.get('op') == 0x100]
cases = []
for inp in inputs:
    candidates = [r for r in renames if key(r) == key(inp)
                  and r.get('pdest') == inp['pdest'] and r['edge'] <= inp['edge']]
    if not candidates:  # rename before the capture window is not evidence
        continue
    rename = max(candidates, key=lambda r: r['edge'])
    if rename['pc'] not in (0x80000322, 0x80000376):
        continue
    reuse = min([r['edge'] for r in renames if key(r) == key(inp)
                 and r['edge'] > inp['edge']] + [metadata['edges'] + 1])
    retired = [c for c in commits if key(c) == key(inp)
               and c.get('pc') == rename['pc'] and inp['edge'] < c['edge'] < reuse]
    if retired or inp['edge'] >= metadata['edges'] - 100:
        continue
    branches = [r for r in renames if r.get('pc') == 0x8000031e
                and rename['edge'] - 10 <= r['edge'] < rename['edge']]
    if not branches:
        continue
    branch = max(branches, key=lambda r: r['edge'])
    redirect = [r for r in redirects if key(r) == key(branch)
                and inp['edge'] < r['edge'] < reuse]
    if len(redirect) != 1:
        continue
    redirect = redirect[0]
    output = one([e for e in events if e['kind'] == 'fu_out' and key(e) == key(inp)
                  and e.get('pdest') == inp['pdest']
                  and inp['edge'] < e['edge'] < redirect['edge']], 'wrong-path FU output')
    writeback = one([e for e in events if e['kind'] == 'writeback'
                     and key(e) == key(inp) and e.get('pdest') == inp['pdest']
                     and e['edge'] == output['edge'] and e['data'] == output['data']], 'wrong-path WB')
    preg = one([e for e in events if e['kind'] == 'preg_write'
                and e.get('pdest') == inp['pdest'] and e['edge'] == output['edge']
                and e['data'] == output['data']], 'wrong-path physical register')
    correct_pc = 0x80000376 if rename['pc'] == 0x80000322 else 0x80000322
    correct = one([r for r in renames if r.get('pc') == correct_pc
                   and r.get('pdest') == inp['pdest']
                   and redirect['edge'] < r['edge'] < redirect['edge'] + 100], 'redirected-path rename')
    correct_commit = one([c for c in commits if key(c) == key(correct)
                          and c.get('pc') == correct_pc
                          and correct['edge'] < c['edge'] < correct['edge'] + 200], 'redirected-path commit')
    branch_commit = one([c for c in commits if key(c) == key(branch)
                         and c.get('pc') == branch['pc']
                         and redirect['edge'] < c['edge'] <= correct_commit['edge']], 'branch commit')
    if correct['ldest'] == rename['ldest']:
        raise ValueError('Paths unexpectedly target the same architectural register')
    if output['edge'] - inp['edge'] != 2:
        raise ValueError('Unexpected vdot FU latency')
    cases.append({'branch_rename': branch, 'wrong_rename': rename,
                  'wrong_input': inp, 'wrong_output': output, 'wrong_writeback': writeback,
                  'wrong_preg_write': preg, 'redirect': redirect,
                  'wrong_rob_epoch_end': reuse, 'wrong_commits_in_epoch': 0,
                  'correct_rename': correct, 'branch_commit': branch_commit,
                  'correct_commit': correct_commit})

if not cases:
    raise SystemExit('No fully observed flushed-vdot case; do not claim coverage')
tagged_inputs = []
for inp in inputs:
    matches = [r for r in renames if key(r) == key(inp) and r.get('pdest') == inp['pdest']
               and r['edge'] <= inp['edge']]
    if matches:
        tagged_inputs.append((inp, max(matches, key=lambda r: r['edge'])))
bursts = []
for start in range(len(tagged_inputs) - 7):
    group = tagged_inputs[start:start + 8]
    if [r.get('ldest') for _, r in group] != list(range(16, 24)):
        continue
    edges = [i['edge'] for i, _ in group]
    if edges != list(range(edges[0], edges[0] + 8)):
        continue
    rows = []
    for inp, rename in group:
        instruction = rename['instr']
        if ((instruction >> 15) & 31) not in range(8, 16) or (instruction >> 20) & 31 != 24:
            raise ValueError('Burst source registers are not independent')
        out = one([e for e in events if e['kind'] == 'fu_out' and key(e) == key(inp)
                   and e.get('pdest') == inp['pdest'] and e['edge'] == inp['edge'] + 2], 'burst result')
        def signed_byte(value, lane):
            byte = (value >> (8 * lane)) & 255
            return byte - 256 if byte >= 128 else byte
        expected = sum(signed_byte(inp['src0'], lane) * signed_byte(inp['src1'], lane)
                       for lane in range(8)) & 0xffffffff
        if out['data'] != expected:
            raise ValueError('Burst result differs from signed-byte software sum or has nonzero high bits')
        next_use = min([r['edge'] for r in renames if key(r) == key(inp)
                        and r['edge'] > inp['edge']] + [metadata['edges'] + 1])
        commit = one([c for c in commits if key(c) == key(inp)
                      and c.get('pc') == rename['pc'] and inp['edge'] < c['edge'] < next_use], 'burst commit')
        rows.append({'input_edge': inp['edge'], 'output_edge': out['edge'],
                     'commit_edge': commit['edge'], 'pc': rename['pc'],
                     'rob_flag': inp['rob_flag'], 'rob_value': inp['rob_value'],
                     'pdest': inp['pdest'], 'ldest': rename['ldest'],
                     'result_hex': f'{expected:032x}'})
    if len({row['pdest'] for row in rows}) != 8:
        raise ValueError('Burst unexpectedly reuses a physical destination')
    bursts.append({'observed_initiation_interval_cycles': 1, 'latency_cycles': 2,
                   'sample_size': 8, 'operations': rows})
if not bursts:
    raise SystemExit('No verified consecutive independent burst; do not claim one-per-cycle throughput')
args.output.mkdir(parents=True, exist_ok=True)
result = {'metadata': metadata, 'completed_pressure_run': str(args.full_run.resolve()),
          'capture_is_functional_pass': False,
          'cases': cases, 'independent_bursts': bursts,
          'coverage_limit': 'These vdots completed FU output before redirect. No claim of redirect while a vdot remains inside its two FU stages.'}
(args.output / 'pipeline-analysis.json').write_text(json.dumps(result, indent=2) + '\n')
with (args.output / 'pipeline-events.csv').open('w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['case', 'stage', 'edge', 'tick', 'pc', 'rob_flag', 'rob_value', 'pdest', 'ldest', 'data'])
    for index, case in enumerate(cases):
        for stage, event in case.items():
            if not isinstance(event, dict):
                continue
            writer.writerow([index, stage, event['edge'], event['tick'],
                             hex(event['pc']) if 'pc' in event else '',
                             event.get('rob_flag', ''), event.get('rob_value', ''),
                             event.get('pdest', ''), event.get('ldest', ''),
                             hex(event['data']) if 'data' in event else ''])
with (args.output / 'burst-throughput.csv').open('w', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=['burst', 'input_edge', 'output_edge', 'commit_edge',
                                             'pc', 'rob_flag', 'rob_value', 'pdest', 'ldest', 'result_hex'])
    writer.writeheader()
    for index, burst in enumerate(bursts):
        writer.writerows({'burst': index, **operation} for operation in burst['operations'])
print(json.dumps({'flushed_after_writeback_cases': len(cases),
                  'verified_independent_bursts': len(bursts), 'observed_burst_initiation_interval_cycles': 1,
                  'vdot_frontend_stall_cycles': metadata.get('vdot_frontend_valid_not_ready_cycles_by_interface', {})}))
