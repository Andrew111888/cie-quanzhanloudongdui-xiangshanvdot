"""Associate whole RVV instructions and their micro-ops in the paired dot FST."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tag(event):
    return tuple(event.get(key) for key in ('rob_flag', 'rob_value', 'pdest'))


def only(values, label):
    if len(values) != 1:
        raise AssertionError((label, len(values)))
    return values[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    args = parser.parse_args()
    run = args.run_directory.resolve(strict=True)
    receipt = json.loads((run / 'results.json').read_text())
    metadata = json.loads((run / 'events/metadata.json').read_text())
    events = json.loads((run / 'events/events.json').read_text())
    assert receipt['status'] == 'passed' and receipt['core_dirty'] == 0
    assert receipt['difftest_enabled'] and receipt['wave_dump_enabled']
    assert digest(run / 'wave.fst') == receipt['fst_sha256'] == metadata['fst_sha256']
    assert digest(run / 'run.log') == receipt['run_log_sha256']
    bound = {}
    for name, pc_text in receipt['instruction_pcs'].items():
        pc = int(pc_text, 16)
        commit = only([e for e in events if e['kind'] == 'commit' and e.get('pc') == pc], name + ' commit')
        renames = [e for e in events if e['kind'] == 'rename' and e.get('pc') == pc
                   and (e.get('rob_flag'), e.get('rob_value')) == (commit['rob_flag'], commit['rob_value'])
                   and e['edge'] <= commit['edge']]
        assert renames and len({e['edge'] for e in renames}) == 1
        start = renames[0]['edge']
        identities = {tag(e) for e in renames}
        window = [e for e in events if start <= e['edge'] <= commit['edge']]
        inputs = [e for e in window if e['kind'] == 'fu_in' and tag(e) in identities]
        outputs = [e for e in window if e['kind'] == 'fu_out' and tag(e) in identities]
        assert len(inputs) == len(outputs) == len(renames)
        for accepted in inputs:
            output = only([e for e in outputs if tag(e) == tag(accepted)], name + ' output')
            assert output['edge'] - accepted['edge'] == 2
            only([e for e in window if e['kind'] == 'writeback' and tag(e) == tag(output)
                  and e['edge'] == output['edge'] and e['data'] == output['data']], name + ' writeback')
            only([e for e in window if e['kind'] == 'preg_write' and e['pdest'] == output['pdest']
                  and e['edge'] == output['edge'] and e['data'] == output['data']], name + ' preg')
        bound[name] = {'pc': pc_text, 'instruction_word': f"{commit['instr']:08x}",
                       'rob': {'flag': commit['rob_flag'], 'value': commit['rob_value']},
                       'renames': renames, 'fu_inputs': inputs, 'fu_outputs': outputs, 'commit': commit}
    dot, mul, reduction = (bound[x] for x in ('vdot.vv', 'baseline_mul', 'baseline_reduce'))
    assert len(dot['fu_inputs']) == 1 and len(mul['fu_inputs']) == len(reduction['fu_inputs']) == 2
    assert {e['ldest'] for e in mul['renames']} == {16, 17}
    assert {e['ldest'] for e in reduction['renames']} == {12, 32}
    partial_product = sum(0x4000 << (16 * i) for i in range(8))
    multiplication_result = only([e for e in mul['fu_outputs'] if e['pdest'] ==
                                 only([r for r in mul['renames'] if r['ldest'] == 16], 'mul lower destination')['pdest']], 'mul lower result')
    assert multiplication_result['data'] == partial_product
    reduce_inputs = sorted(reduction['fu_inputs'], key=lambda e: e['uop'])
    assert [e['uop'] for e in reduce_inputs] == [0, 1]
    assert reduce_inputs[0]['src1'] == multiplication_result['data']
    intermediate = only([e for e in reduction['fu_outputs'] if e['pdest'] == reduce_inputs[0]['pdest']], 'partial reduction')
    assert reduce_inputs[1]['src1'] == intermediate['data'] and reduce_inputs[1]['src0'] == 0
    final_pdest = only([e for e in reduction['renames'] if e['ldest'] == 12], 'architectural destination')['pdest']
    final = only([e for e in reduction['fu_outputs'] if e['pdest'] == final_pdest], 'full reduction result')
    dot_output = only(dot['fu_outputs'], 'dot result')
    assert final['data'] == dot_output['data'] == 131072
    dot_latency = dot_output['edge'] - dot['fu_inputs'][0]['edge']
    first_multiply = min(mul['fu_inputs'], key=lambda e: e['edge'])
    baseline_span = final['edge'] - first_multiply['edge']
    assert baseline_span > 0 and dot_latency > 0
    result = {'status': 'passed', 'scope': 'one_paired_eight_int8_execution_span',
              'core_commit': receipt['core_commit'], 'core_dirty': 0,
              'fst_sha256': receipt['fst_sha256'], 'run_log_sha256': receipt['run_log_sha256'],
              'timescale': metadata['timescale'], 'sampling': metadata['sampling'],
              'instructions': bound, 'vdot_execution_cycles': dot_latency,
              'rvv_execution_span_cycles': baseline_span, 'observed_span_ratio': baseline_span / dot_latency,
              'rvv_span_begin': first_multiply, 'rvv_span_end': final,
              'result_hex': f'{131072:032x}',
              'boundary': 'source loads and destination/seed zeroing are outside; RVV interval is first multiply FU acceptance through final reduction FU output, including intermediate micro-ops and scheduling',
              'reduction_commit_debug_destination_is_internal_first_microop': reduction['commit']['ldest'] == 32}
    (run / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'scope', 'vdot_execution_cycles', 'rvv_execution_span_cycles', 'observed_span_ratio', 'result_hex')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
