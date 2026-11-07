"""Associate committed vdot/vdot.acc instructions with their real FST events."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(event):
    return tuple(event.get(name) for name in ('rob_flag', 'rob_value', 'pdest'))


def only(events, label):
    if len(events) != 1:
        raise AssertionError((label, len(events)))
    return events[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    args = parser.parse_args()
    run = args.run_directory.resolve(strict=True)
    receipt = json.loads((run / 'results.json').read_text())
    metadata = json.loads((run / 'events/metadata.json').read_text())
    events = json.loads((run / 'events/events.json').read_text())
    assert receipt['status'] == 'passed' and receipt['scope'] == 'rtl_nemu_difftest'
    assert receipt['wave_dump_enabled'] and receipt['difftest_enabled'] and receipt['core_dirty'] == 0
    assert digest(run / 'wave.fst') == receipt['fst_sha256'] == metadata['fst_sha256']
    probes = []
    for name, instruction, operation, expected in (
        ('vdot.vv', 0x02a4060b, 0x100, 8),
        ('vdot.acc', 0x06a4060b, 0x101, 0x12345680),
    ):
        pc = int(receipt['instruction_pcs'][name], 16)
        commit = only([e for e in events if e['kind'] == 'commit'
                       and e.get('pc') == pc and e.get('instr') == instruction], name + ' commit')
        assert commit['ldest'] == 12 and commit['vecwen'] == 1
        tag = identity(commit)
        renames = [e for e in events if e['kind'] == 'rename' and identity(e) == tag
                   and e.get('pc') == pc and e.get('instr') == instruction
                   and e['edge'] <= commit['edge']]
        assert renames
        rename = max(renames, key=lambda e: e['edge'])
        current = [e for e in events if rename['edge'] <= e['edge'] <= commit['edge']]
        accepted = only([e for e in current if e['kind'] == 'fu_in'
                         and '.Vimac' in e['source'] and identity(e) == tag
                         and e.get('op') == operation], name + ' FU input')
        result = only([e for e in current if e['kind'] == 'fu_out'
                       and '.Vimac' in e['source'] and identity(e) == tag
                       and e['edge'] >= accepted['edge']], name + ' FU output')
        assert result['data'] == expected
        assert accepted['src0'] & ((1 << 64) - 1) == 0x0101010101010101
        assert accepted['src1'] & ((1 << 64) - 1) == 0x0101010101010101
        if name == 'vdot.acc':
            assert accepted['src2'] & 0xffffffff == 0x12345678
        writeback = only([e for e in current if e['kind'] == 'writeback'
                          and identity(e) == tag and e.get('data') == expected
                          and e['edge'] == result['edge']], name + ' writeback')
        preg = only([e for e in current if e['kind'] == 'preg_write'
                     and e.get('pdest') == tag[2] and e.get('data') == expected
                     and e['edge'] == result['edge']], name + ' physical register write')
        decodes = [e for e in events if e['kind'] == 'decode' and e.get('pc') == pc
                   and e.get('instr') == instruction and e['edge'] <= rename['edge']]
        decode = max(decodes, key=lambda e: e['edge']) if decodes else None
        issues = [e for e in current if e['kind'] == 'issue' and identity(e) == tag
                  and e.get('op') == operation and e['edge'] <= accepted['edge']]
        probes.append({'instruction': name, 'pc': hex(pc), 'instruction_word': f'{instruction:08x}',
                       'logical_destination': 'v12',
                       'rob': {'flag': tag[0], 'value': tag[1]}, 'physical_destination': tag[2],
                       'decode': decode, 'rename': rename, 'issue': issues,
                       'fu_input': accepted, 'fu_output': result, 'writeback': writeback,
                       'physical_register_write': preg, 'commit': commit,
                       'input_to_output_cycles': result['edge'] - accepted['edge'],
                       'output_to_commit_cycles': commit['edge'] - result['edge'],
                       'result_hex': f'{expected:032x}'})
    result = {'status': 'passed', 'implementation': 'current_shared_dot_acc_retimed_prefix',
              'core_commit': receipt['core_commit'], 'core_dirty': 0,
              'fst': str(run / 'wave.fst'), 'fst_sha256': receipt['fst_sha256'],
              'run_log_sha256': receipt['run_log_sha256'], 'timescale': metadata['timescale'],
              'sampling': metadata['sampling'], 'probes': probes}
    (run / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': 'passed', 'directory': str(run), 'probes': [
        {k: p[k] for k in ('instruction', 'pc', 'rob', 'physical_destination',
                          'input_to_output_cycles', 'result_hex')} for p in probes]},
        ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
