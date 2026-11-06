"""Join vector-load rename, issue, writeback and commit events from a real FST."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('run', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
fst = args.run / 'wave.fst'
loops = json.loads((args.run / 'loop-audit.json').read_text())
args.output.mkdir(parents=True, exist_ok=True)
backend = 'TOP.SimTop.cpu.l_soc.core_with_l2.core.backend'
groups = {}
selected = {}
clock = reset = commit_enable = None
scope = []
timescale = []


def field(raw):
    raw = raw.removeprefix('bits_')
    raw = raw.removeprefix('ctrl_').removeprefix('common_')
    raw = raw.removeprefix('basicDebug_').removeprefix('debug_').removeprefix('vpu_')
    aliases = {'robIdx_flag': 'rob_flag', 'robIdx_value': 'rob_value',
               'fuType': 'fu_type', 'vecWen': 'vecwen'}
    raw = aliases.get(raw, raw)
    if raw in {'valid', 'ready', 'pc', 'pdest', 'ldest', 'rob_flag', 'rob_value',
               'vecwen', 'fu_type', 'vl', 'vta', 'vm', 'vuopIdx', 'firstUop', 'lastUop'}:
        return raw
    if re.fullmatch(r'(?:psrc|srcType|srcState|lsrc)_\d', raw):
        return raw
    if re.fullmatch(r'rf_\d_0_(?:addr|srcType)', raw):
        return raw


def select(parts):
    global clock, reset, commit_enable
    name = '.'.join(scope + [parts[4]])
    short = name.removeprefix(backend + '.')
    item = {'name': name, 'width': int(parts[2]), 'code': parts[3]}
    if name == backend + '.clock':
        clock = parts[3]; selected[name] = item
    elif name == backend + '.reset':
        reset = parts[3]; selected[name] = item
    elif short == 'inner_ctrlBlock.rob.io_commits_isCommit':
        commit_enable = parts[3]; selected[name] = item
    if not name.startswith(backend + '.'):
        return
    patterns = (
        ('rename', r'(inner_ctrlBlock\.rename\.io_out_\d+)_(.+)'),
        ('issue', r'(inner_memScheduler\.io_toDataPathAfterDelay_\d+_\d+)_(.+)'),
        ('writeback', r'(inner_wbDataPath\.io_toCtrlBlock_writeback_\d+)_(.+)'),
    )
    for kind, pattern in patterns:
        match = re.fullmatch(pattern, short)
        if match:
            key = field(match[2])
            if key:
                group = groups.setdefault((kind, match[1]), {})
                group[key] = parts[3]; selected[name] = item
            return
    patterns = (
        (r'inner_ctrlBlock\.rob\.io_commits_commitValid_(\d+)', 'valid'),
        (r'inner_ctrlBlock\.rob\.io_commits_robIdx_(\d+)_(.+)', 'robIdx_'),
        (r'inner_ctrlBlock\.rob\.io_commits_info_(\d+)_(.+)', ''),
    )
    for pattern, prefix in patterns:
        match = re.fullmatch(pattern, short)
        if match:
            key = field(prefix + (match[2] if len(match.groups()) > 1 else ''))
            if key:
                group = groups.setdefault(('commit', 'commit_' + match[1]), {})
                group[key] = parts[3]; selected[name] = item
            return


events = []
state = {}
changes = {}
edge = timestamp = 0


def finish_timestamp():
    global edge
    if state.get(clock) == 0 and changes.get(clock, state.get(clock)) == 1:
        edge += 1
        if state.get(reset) == 0:
            for (kind, source), signals in groups.items():
                if state.get(signals.get('valid')) != 1:
                    continue
                if 'ready' in signals and state.get(signals['ready']) != 1:
                    continue
                if kind == 'commit' and state.get(commit_enable) != 1:
                    continue
                values = {key: state.get(code) for key, code in signals.items()}
                if kind == 'writeback' and values.get('vecwen') != 1:
                    continue
                events.append({'kind': kind, 'source': source, 'edge': edge, 'tick': timestamp, **values})
    state.update(changes); changes.clear()


with (args.output / 'fst2vcd.stderr').open('w') as errors:
    process = subprocess.Popen(['fst2vcd', str(fst)], stdout=subprocess.PIPE, stderr=errors,
                               text=True, bufsize=1024 * 1024)
    in_scale = False
    for line in process.stdout:
        parts = line.split()
        if parts[:1] == ['$scope']: scope.append(parts[2])
        elif parts[:1] == ['$upscope']: scope.pop()
        elif parts[:1] == ['$var']: select(parts)
        elif parts[:1] == ['$timescale']:
            timescale.extend(s for s in parts[1:] if s != '$end'); in_scale = '$end' not in parts
        elif in_scale:
            timescale.extend(s for s in parts if s != '$end'); in_scale = '$end' not in parts
        elif parts[:1] == ['$enddefinitions']: break
    assert clock and reset and commit_enable
    wanted = {s['code'] for s in selected.values()}
    for line in process.stdout:
        line = line.strip()
        if not line or line.startswith('$'): continue
        if line.startswith('#'):
            finish_timestamp(); timestamp = int(line[1:])
        elif line[0] in '01xXzZ' and line[1:] in wanted:
            changes[line[1:]] = int(line[0]) if line[0] in '01' else None
        elif line[0] in 'bB':
            value, code = line[1:].split()
            if code in wanted: changes[code] = None if re.search('[xzXZ]', value) else int(value, 2)
    finish_timestamp(); assert process.wait() == 0

(args.output / 'signals.json').write_text(json.dumps(list(selected.values()), indent=2) + '\n')
(args.output / 'events.json').write_text(json.dumps(events, indent=2) + '\n')


def region(pc):
    if pc is None: return None
    return next((name for name, bounds in loops.items()
                 if int(bounds['begin_pc'], 16) <= pc <= int(bounds['branch_pc'], 16)), None)


# One architectural vector instruction can rename several micro-operations.
# firstUop starts a ROB lifetime; pdest distinguishes its micro-operations.
active = {}
lifetimes = []
for event in sorted(events, key=lambda e: (e['edge'], {'rename': 0, 'issue': 1, 'writeback': 2, 'commit': 3}[e['kind']])):
    tag = (event.get('rob_flag'), event.get('rob_value'))
    if None in tag: continue
    if event['kind'] == 'rename':
        assert event.get('firstUop') is not None
        if event['firstUop'] or tag not in active:
            active[tag] = {'pcs': set(), 'uops': [], 'commit': []}
        group = active[tag]
        group['pcs'].add(event.get('pc'))
        lifetime = {'rename': event, 'issue': [], 'writeback': [], 'group': group}
        lifetimes.append(lifetime); group['uops'].append(lifetime)
    else:
        group = active.get(tag)
        if group is None: continue
        if event['kind'] == 'commit':
            if event.get('pc') is not None:
                assert event['pc'] in group['pcs']
            group['commit'].append(event)
        else:
            for lifetime in group['uops']:
                if event.get('pdest') == lifetime['rename'].get('pdest'):
                    lifetime[event['kind']].append(event)

loads = []
previous = {}
for lifetime in lifetimes:
    rename = lifetime['rename']; name = region(rename.get('pc'))
    if name is None or rename.get('vecwen') != 1 or rename.get('ldest') not in {8,10,16,18,20,22,24,26}:
        continue
    if not lifetime['issue'] or not lifetime['writeback'] or not lifetime['group']['commit']:
        continue
    issue = min(lifetime['issue'], key=lambda e: e['edge'])
    wb = min(lifetime['writeback'], key=lambda e: e['edge'])
    row = {'kernel': name, 'pc': hex(rename['pc']), 'ldest': rename['ldest'],
           'rob_flag': rename['rob_flag'], 'rob_value': rename['rob_value'],
           'pdest': rename['pdest'], 'old_vd_psrc': rename.get('psrc_2'),
           'rename_edge': rename['edge'], 'issue_edge': issue['edge'], 'writeback_edge': wb['edge'],
           'commit_edge': lifetime['group']['commit'][0]['edge'], 'issue_old_vd_type': issue.get('srcType_2'),
           'issue_old_vd_read_address': issue.get('rf_2_0_addr'),
           'issue_source': issue['source'], 'vta': rename.get('vta')}
    prior = previous.get((name, rename['ldest']))
    if prior is not None:
        row.update(previous_pdest=prior['pdest'], previous_writeback_edge=prior['writeback_edge'],
                   old_vd_matches_previous=rename.get('psrc_2') == prior['pdest'],
                   issue_gap_from_previous=issue['edge'] - prior['issue_edge'],
                   issue_after_previous_writeback=issue['edge'] - prior['writeback_edge'])
    previous[(name, rename['ldest'])] = row
    loads.append(row)
assert loads
summaries = []
for name in sorted({row['kernel'] for row in loads}):
    rows = [row for row in loads if row['kernel'] == name]
    chained = [row for row in rows if row.get('old_vd_matches_previous')]
    summaries.append({'kernel': name, 'committed_loads': len(rows),
                      'issue_old_vd_types': sorted({row['issue_old_vd_type'] for row in rows}, key=str),
                      'matched_previous_destinations': len(chained),
                      'median_same_destination_issue_gap': statistics.median(row['issue_gap_from_previous'] for row in chained) if chained else None,
                      'minimum_issue_after_previous_writeback': min(row['issue_after_previous_writeback'] for row in chained) if chained else None})
metadata = {'status': 'extracted', 'fst': str(fst.resolve()),
            'fst_sha256': hashlib.sha256(fst.read_bytes()).hexdigest(), 'timescale': ' '.join(timescale),
            'sampling': 'immediately before rising backend clock edge', 'edges': edge,
            'selected_signals': len(selected), 'event_count': len(events), 'summaries': summaries}
(args.output / 'signals.json').write_text(json.dumps(list(selected.values()), indent=2) + '\n')
(args.output / 'events.json').write_text(json.dumps(events, indent=2) + '\n')
(args.output / 'loads.json').write_text(json.dumps(loads, indent=2) + '\n')
(args.output / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
print(json.dumps(metadata, ensure_ascii=False), flush=True)
