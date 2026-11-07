"""Correlate mixed-vector handshakes by ROB allocation episode and physical destination.

A redirect is linked to the most recent rename of its ROB tag. Speculative dot
instructions are reported separately from dots actually resident in execution.
Interface-wide stall counts are not evidence of custom-dot backpressure.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    result = json.loads((run / 'results.json').read_text())
    assert result['status'] == 'passed' and result['difftest_enabled']
    fst = Path(result['fst'])
    assert sha(fst) == result['fst_sha256']
    directory = run / 'events'
    extractor = Path(__file__).with_name('extract_wave_events.py')
    if not (directory / 'events.json').exists():
        subprocess.run([sys.executable, str(extractor), str(fst), '--output', str(directory)], check=True)
    meta = json.loads((directory / 'metadata.json').read_text())
    assert meta['fst_sha256'] == sha(fst)
    events = json.loads((directory / 'events.json').read_text())
    pcs = {name: int(pc, 16) for name, pc in result['instruction_pcs'].items()}
    names = {pc: name for name, pc in pcs.items()}
    tag = lambda e: (e.get('rob_flag'), e.get('rob_value'))
    ident = lambda e: (*tag(e), e.get('pdest'))
    renames = [e for e in events if e['kind'] == 'rename']
    allocations = {}
    for e in renames:
        allocations.setdefault(tag(e), []).append(e)
    episodes = []
    for e in renames:
        if e.get('pc') not in names or e.get('op') not in (0x100, 0x101) or not e.get('vecwen'):
            continue
        following = [v for v in allocations[tag(e)] if v['edge'] > e['edge']]
        end = following[0]['edge'] if following else meta['edges'] + 1
        matched = [v for v in events if e['edge'] <= v['edge'] < end and ident(v) == ident(e)]
        by_kind = {}
        for v in matched:
            by_kind.setdefault(v['kind'], []).append(v)
        episodes.append({'name': names[e['pc']], 'pc': hex(e['pc']), 'rob_flag': e['rob_flag'],
                         'rob_value': e['rob_value'], 'pdest': e['pdest'], 'rename_edge': e['edge'],
                         'next_allocation_edge': end if following else None,
                         'events': by_kind})
    redirects = []
    for e in events:
        if e['kind'] != 'redirect':
            continue
        prior = [v for v in allocations.get(tag(e), []) if v['edge'] <= e['edge']]
        origin = prior[-1] if prior else None
        if origin is None or origin.get('pc') != pcs['control_branch']:
            continue
        candidates = []
        for ep in episodes:
            if not (origin['edge'] < ep['rename_edge'] < e['edge']):
                continue
            if ep['next_allocation_edge'] is not None and ep['next_allocation_edge'] <= e['edge']:
                continue
            # Only the two branch arms, not unrelated future scalar-loop instructions.
            if ep['name'] not in ('control_taken_acc', 'control_taken_dot', 'control_other_acc', 'control_other_dot'):
                continue
            commits = ep['events'].get('commit', [])
            if any(v['edge'] <= e['edge'] for v in commits):
                continue
            accepted = [v for v in ep['events'].get('fu_in', []) if v['edge'] < e['edge']]
            completed = [v for v in ep['events'].get('exu_out', []) if v['edge'] <= e['edge']]
            # A later ROB reuse closes the observation interval; otherwise this is only bounded evidence.
            closed = ep['next_allocation_edge'] is not None
            candidates.append({'name': ep['name'], 'pc': ep['pc'],
                               'rob_flag': ep['rob_flag'], 'rob_value': ep['rob_value'], 'pdest': ep['pdest'],
                               'rename_edge': ep['rename_edge'], 'accepted_fu_edges': [v['edge'] for v in accepted],
                               'completed_exu_edges': [v['edge'] for v in completed],
                               'execution_resident_at_redirect': bool(accepted and not completed),
                               'commits_before_next_allocation': [v['edge'] for v in commits],
                               'observation_closed_by_reallocation': closed,
                               'no_commit_before_reallocation': closed and not commits,
                               'allocation_end_edge': ep['next_allocation_edge']})
        redirects.append({'redirect': e, 'branch_rename': origin, 'speculative_dot_candidates': candidates})
    closed = [c for r in redirects for c in r['speculative_dot_candidates'] if c['no_commit_before_reallocation']]
    resident = [c for c in closed if c['execution_resident_at_redirect']]
    committed = Counter(names.get(e.get('pc')) for e in events if e['kind'] == 'commit' and e.get('pc') in names)
    output = {'status': 'passed', 'scope': 'bounded whole-core FST plus complete program RTL/NEMU differential run',
              'fst_sha256': sha(fst), 'results_sha256': sha(run / 'results.json'),
              'analyzer_sha256': sha(Path(__file__)), 'capture_begin': result['capture_begin'],
              'capture_end': result['capture_end'], 'sampling': meta['sampling'],
              'mixed_instruction_commit_counts_in_capture': dict(committed),
              'custom_rename_episodes_in_capture': len(episodes), 'branch_redirect_count': len(redirects),
              'squashed_custom_allocations_closed_by_rob_reuse': len(closed),
              'custom_fu_resident_at_redirect_closed_by_rob_reuse': len(resident),
              'custom_execution_stage_flush_covered': bool(resident),
              'speculative_custom_rob_flush_covered': bool(closed),
              'custom_backpressure_covered': False,
              'backpressure_note': 'Interface counts below include other vector operations; no custom-tag valid&&!ready proof is claimed.',
              'valid_not_ready_cycles_by_interface': meta['valid_not_ready_cycles_by_interface'],
              'vdot_frontend_valid_not_ready_cycles_by_interface': meta['vdot_frontend_valid_not_ready_cycles_by_interface'],
              'redirects': redirects, 'custom_episodes': episodes}
    (run / 'control-analysis.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in output.items() if k not in ('custom_episodes', 'redirects', 'valid_not_ready_cycles_by_interface')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
