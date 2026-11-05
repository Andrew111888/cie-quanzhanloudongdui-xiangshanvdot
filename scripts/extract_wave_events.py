"""Stream a real FST through fst2vcd and record backend interface handshakes.

Values are sampled immediately BEFORE each rising backend clock edge. A leaf
FU input gets its ROB tag from the same parent Exu input, never ctrlPipe_N.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from collections import Counter

parser = argparse.ArgumentParser()
parser.add_argument('fst', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
backend = 'TOP.SimTop.cpu.l_soc.core_with_l2.core.backend'
groups = {}
selected = {}
clock_codes = {}
reset_codes = {}
commit_enable = None


def normalize(raw):
    raw = raw.removeprefix('bits_')
    if raw.startswith('ctrlPipe_'):
        return None
    raw = raw.removeprefix('ctrl_').removeprefix('common_')
    raw = raw.removeprefix('basicDebug_').removeprefix('debug_')
    raw = raw.removeprefix('vpu_')
    aliases = {'robIdx_flag': 'rob_flag', 'robIdx_value': 'rob_value',
               'fuOpType': 'op', 'fuType': 'fu_type', 'vecWen': 'vecwen',
               'res_data': 'data', 'data_0': 'data', 'addr': 'pdest',
               'wen': 'valid', 'data_src_0': 'src0', 'data_src_1': 'src1',
               'data_src_2': 'src2', 'src_0': 'src0', 'src_1': 'src1',
               'src_2': 'src2', 'data_src_3': 'src3', 'data_src_4': 'src4',
               'src_3': 'src3', 'src_4': 'src4', 'vuopIdx': 'uop'}
    raw = aliases.get(raw, raw)
    return raw if raw in {'valid', 'ready', 'pc', 'instr', 'pdest', 'ldest',
                         'rob_flag', 'rob_value', 'op', 'fu_type', 'vecwen',
                         'data', 'src0', 'src1', 'src2', 'src3', 'src4', 'vsew', 'vlmul',
                         'vl', 'vm', 'vstart', 'vta', 'vma', 'uop'} else None


def register(kind, source, raw, signal, parent=None):
    field = normalize(raw)
    if field is None:
        return
    group = groups.setdefault((kind, source), {'kind': kind, 'source': source,
                                              'fields': {}, 'parent': parent})
    group['fields'][field] = signal['code']
    selected[signal['name']] = signal


def select(signal):
    global commit_enable
    name = signal['name']
    if name in ('TOP.clock', backend + '.clock'):
        clock_codes[name] = signal['code']; selected[name] = signal
    if name in ('TOP.reset', backend + '.reset'):
        reset_codes[name] = signal['code']; selected[name] = signal
    if not name.startswith(backend + '.'):
        return
    short = name[len(backend) + 1:]
    if short == 'inner_ctrlBlock.rob.io_commits_isCommit':
        commit_enable = signal['code']; selected[name] = signal
    patterns = (
        ('decode', r'(inner_ctrlBlock\.decode\.io_in_\d+)_(.+)'),
        ('rename', r'(inner_ctrlBlock\.rename\.io_out_\d+)_(.+)'),
        ('issue', r'(inner_vfScheduler\.io_toDataPathAfterDelay_\d+_\d+)_(.+)'),
        ('writeback', r'(inner_wbDataPath\.io_toCtrlBlock_writeback_\d+)_(.+)'),
        ('preg_write', r'(inner_wbDataPath\.io_toVfPreg_\d+)_(.+)'),
        ('redirect', r'(inner_ctrlBlock\.io_redirect)_(.+)'),
    )
    for kind, pattern in patterns:
        m = re.fullmatch(pattern, short)
        if m:
            register(kind, m[1], m[2], signal)
            return
    m = re.fullmatch(r'inner_vfExuBlock\.(exus(?:_\d+)?)(?:\.([^.]+))?\.io_(in|out)_(.+)', short)
    if m:
        instance, leaf, direction, raw = m.groups()
        if leaf and leaf not in {'Vimac', 'VialuFix', 'Vipu', 'Vfma', 'Vfalu',
                                 'Vfcvt', 'VSetRvfWvf', 'Vppu', 'Vfdiv', 'Vidiv'}:
            return
        parent = 'inner_vfExuBlock.' + instance
        source = parent + ('.' + leaf if leaf else '')
        register(('fu_' if leaf else 'exu_') + direction, source, raw, signal,
                 parent if leaf else None)
        return
    for pattern, suffix in (
        (r'inner_ctrlBlock\.rob\.io_commits_commitValid_(\d+)', 'valid'),
        (r'inner_ctrlBlock\.rob\.io_commits_robIdx_(\d+)_(.+)', 'robIdx_'),
        (r'inner_ctrlBlock\.rob\.io_commits_info_(\d+)_(.+)', ''),
    ):
        m = re.fullmatch(pattern, short)
        if m:
            raw = suffix + (m[2] if len(m.groups()) > 1 else '')
            register('commit', 'inner_ctrlBlock.rob.commit_' + m[1], raw, signal)
            return


events = []
stalls = Counter()
vdot_frontend_stalls = Counter()
state = {}
changes = {}
edge = 0
timestamp = 0


def values(group):
    return {key: state.get(code) for key, code in group['fields'].items()}


def finish_timestamp():
    global edge
    clock = clock_codes.get(backend + '.clock', clock_codes.get('TOP.clock'))
    if state.get(clock) == 0 and changes.get(clock, state.get(clock)) == 1:
        edge += 1
        reset = reset_codes.get(backend + '.reset', reset_codes.get('TOP.reset'))
        if state.get(reset) == 0:
            for group in groups.values():
                data = values(group)
                if data.get('valid') == 1 and data.get('ready') == 0:
                    stalls[group['kind'] + ':' + group['source']] += 1
                    decoded_dot = group['kind'] == 'decode' and data.get('instr') is not None and data['instr'] & 0xfc00707f == 0x0000000b
                    renamed_dot = group['kind'] == 'rename' and data.get('vecwen') == 1 and data.get('op') == 0x100
                    if decoded_dot or renamed_dot:
                        vdot_frontend_stalls[group['kind'] + ':' + group['source']] += 1
                if data.get('valid') != 1 or ('ready' in data and data['ready'] != 1):
                    continue
                kind = group['kind']
                if kind == 'commit' and state.get(commit_enable) != 1:
                    continue
                if kind in ('writeback', 'preg_write') and data.get('vecwen') != 1:
                    continue
                if kind == 'fu_in':
                    parent = groups.get(('exu_in', group['parent']))
                    if parent is None:
                        raise RuntimeError('Missing parent Exu interface: ' + group['source'])
                    current = values(parent)
                    if current.get('valid') != 1 or current.get('ready') != 1:
                        raise RuntimeError('Leaf input handshake without parent acceptance: ' + group['source'])
                    for key in ('rob_flag', 'rob_value', 'pdest'):
                        data[key] = current.get(key)
                events.append({'edge': edge, 'tick': timestamp, 'kind': kind,
                               'source': group['source'], **data})
    state.update(changes)
    changes.clear()


with (args.output / 'fst2vcd.stderr').open('w') as errors:
    process = subprocess.Popen(['/usr/bin/fst2vcd', str(args.fst)],
                               stdout=subprocess.PIPE, stderr=errors, text=True,
                               bufsize=1024 * 1024)
    scope = []
    timescale = []
    in_timescale = False
    for line in process.stdout:
        words = line.split()
        if words[:1] == ['$scope']:
            scope.append(words[2])
        elif words[:1] == ['$upscope']:
            scope.pop()
        elif words[:1] == ['$var']:
            select({'name': '.'.join(scope + [words[4]]), 'width': int(words[2]), 'code': words[3]})
        elif words[:1] == ['$timescale']:
            in_timescale = True
            timescale.extend(w for w in words[1:] if w != '$end')
            if '$end' in words: in_timescale = False
        elif in_timescale:
            timescale.extend(w for w in words if w != '$end')
            if '$end' in words: in_timescale = False
        elif words[:1] == ['$enddefinitions']:
            break
    if not clock_codes or not reset_codes or commit_enable is None:
        raise SystemExit('Missing clock/reset/commit signals; cannot interpret this trace')
    wanted = {s['code'] for s in selected.values()}
    for line in process.stdout:
        line = line.strip()
        if not line or line.startswith('$'):
            continue
        if line.startswith('#'):
            finish_timestamp()
            timestamp = int(line[1:])
        elif line[0] in '01xXzZ':
            if line[1:] in wanted:
                changes[line[1:]] = int(line[0]) if line[0] in '01' else None
        elif line[0] in 'bB':
            bits, code = line[1:].split()
            if code in wanted:
                changes[code] = None if re.search('[xzXZ]', bits) else int(bits, 2)
    finish_timestamp()
    status = process.wait()
    if status:
        raise SystemExit(f'fst2vcd exited {status}; inspect fst2vcd.stderr')

metadata = {'fst': str(args.fst.resolve()),
            'fst_sha256': hashlib.sha256(args.fst.read_bytes()).hexdigest(),
            'timescale': ' '.join(timescale), 'sampling': 'before rising backend clock edge',
            'clock': backend + '.clock' if backend + '.clock' in clock_codes else 'TOP.clock',
            'edges': edge, 'event_count': len(events), 'selected_signals': len(selected),
            'valid_not_ready_cycles_by_interface': dict(sorted(stalls.items())),
            'vdot_frontend_valid_not_ready_cycles_by_interface': dict(sorted(vdot_frontend_stalls.items()))}
(args.output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
(args.output / 'signals.json').write_text(json.dumps(list(selected.values()), indent=2) + '\n')
(args.output / 'events.json').write_text(json.dumps(events, indent=2) + '\n')
print(json.dumps(metadata))
