"""Validate instruction identity and summarize real extracted interface events.

Run extract_wave_events.py first. ROB tags are circular: matching is bounded by
the last rename of the committed PC and its commit, rather than by tag alone.
The SVG shows sampled handshakes, not reconstructed continuous signal levels.
"""
import argparse
import csv
import html
import json
from pathlib import Path


def require_one(items, description):
    if len(items) != 1:
        raise ValueError(f'{description}: expected one event, got {len(items)}')
    return items[0]


def trace(events, pc):
    commit = require_one([e for e in events if e['kind'] == 'commit'
                          and e.get('pc') == pc], f'commit PC {pc:#x}')
    tag = commit['rob_flag'], commit['rob_value']
    renames = [e for e in events if e['kind'] == 'rename' and e.get('pc') == pc
               and (e.get('rob_flag'), e.get('rob_value')) == tag
               and e['edge'] <= commit['edge']]
    anchor = max(e['edge'] for e in renames)
    renames = [e for e in renames if e['edge'] == anchor]
    selected = [e for e in events if anchor <= e['edge'] <= commit['edge']
                and (e.get('rob_flag'), e.get('rob_value')) == tag]
    decode = max((e for e in events if e['kind'] == 'decode'
                  and e.get('pc') == pc and e.get('instr') == commit['instr']
                  and e['edge'] <= anchor), key=lambda e: e['edge'])
    writes = []
    for out in [e for e in selected if e['kind'] == 'fu_out']:
        wb = require_one([e for e in selected if e['kind'] == 'writeback'
                          and e['edge'] == out['edge']
                          and e['pdest'] == out['pdest']
                          and e['data'] == out['data']], 'FU/writeback identity')
        preg = require_one([e for e in events if e['kind'] == 'preg_write'
                            and e['edge'] == wb['edge']
                            and e['pdest'] == wb['pdest']
                            and e['data'] == wb['data']], 'physical register write')
        writes.append(preg)
    if not writes:
        raise ValueError('No verified vector register writes')
    return {'pc': pc, 'rob_flag': tag[0], 'rob_value': tag[1],
            'decode': decode, 'renames': renames, 'commit': commit,
            'events': [decode] + selected + writes}


def pairs(instruction):
    events = instruction['events']
    result = []
    for inp in [e for e in events if e['kind'] == 'fu_in']:
        out = require_one([e for e in events if e['kind'] == 'fu_out'
                           and e['pdest'] == inp['pdest']
                           and e['source'] == inp['source']
                           and e['edge'] >= inp['edge']], 'FU input/output pair')
        result.append({'pdest': inp['pdest'], 'uop': inp['uop'],
                       'fu': inp['source'], 'input_edge': inp['edge'],
                       'output_edge': out['edge'],
                       'cycles': out['edge'] - inp['edge'],
                       'result_hex': f'{out["data"]:032x}'})
    return result


def event_table(path, instructions):
    fields = ['instruction', 'edge', 'tick', 'kind', 'source', 'rob_flag',
              'rob_value', 'pdest', 'ldest', 'uop', 'op', 'data_hex']
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for label, instruction in instructions.items():
            for event in sorted(instruction['events'], key=lambda e: e['edge']):
                row = {k: event[k] for k in fields if k in event}
                row['instruction'] = label
                if 'data' in event:
                    row['data_hex'] = f'{event["data"]:032x}'
                writer.writerow(row)


def diagram(path, title, rows):
    first = min(edge for _, edge, _, _ in rows)
    last = max(edge for _, edge, _, _ in rows)
    left, width = 340, 720
    height = 140 + len(rows) * 38
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1140" height="{height}" viewBox="0 0 1140 {height}">',
             '<rect width="100%" height="100%" fill="#fff"/>',
             '<style>text{font-family:DejaVu Sans,Arial,sans-serif;fill:#182b49;font-size:14px}.small{font-size:12px;fill:#52647d}</style>',
             f'<text x="24" y="30" style="font-size:20px;font-weight:bold">{html.escape(title)}</text>',
             '<text x="24" y="54" class="small">Real FST handshakes; sampled before rising backend clock edges. Dots are events, not continuous signal levels.</text>']
    for edge in range(first, last + 1):
        x = left + (edge - first) / max(last - first, 1) * width
        lines.append(f'<line x1="{x}" x2="{x}" y1="78" y2="{height-46}" stroke="#e6ebf2"/>')
        if edge in (first, last) or (edge - first) % 4 == 0:
            lines.append(f'<text x="{x}" y="{height-24}" text-anchor="middle" class="small">{edge}</text>')
    for i, (label, edge, color, note) in enumerate(rows):
        y = 96 + i * 38
        x = left + (edge - first) / max(last - first, 1) * width
        lines += [f'<text x="24" y="{y+5}">{html.escape(label)}</text>',
                  f'<circle cx="{x}" cy="{y}" r="6" fill="{color}"/>',
                  f'<text x="{x+10 if x < 970 else x-10}" y="{y-10}" text-anchor="{"start" if x<970 else "end"}" class="small">edge {edge}: {html.escape(note)}</text>']
    lines.append('</svg>')
    path.write_text('\n'.join(lines) + '\n')


parser = argparse.ArgumentParser()
parser.add_argument('--vadd-events', type=Path, required=True)
parser.add_argument('--latency-events', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
vadd_events = json.loads((args.vadd_events / 'events.json').read_text())
latency_events = json.loads((args.latency_events / 'events.json').read_text())
vadd = trace(vadd_events, 0x80000118)
multiply = trace(latency_events, 0x800000ba)
reduce = trace(latency_events, 0x800000ca)
vdot = trace(latency_events, 0x800000e2)
vadd_pairs, mul_pairs, red_pairs, dot_pairs = map(pairs, (vadd, multiply, reduce, vdot))
if len(vadd_pairs) != 1 or vadd_pairs[0]['result_hex'] != '34302c2824201c1814100c080400fcf8':
    raise ValueError('vadd result or micro-operation count differs')
if len(dot_pairs) != 1 or dot_pairs[0]['result_hex'] != '00000000000000000000000000000008':
    raise ValueError('vdot result or micro-operation count differs')
if {p['uop'] for p in mul_pairs} != {0, 1} or {p['uop'] for p in red_pairs} != {0, 1}:
    raise ValueError('Expected both widening/reduction micro-operations')
final_red = require_one([p for p in red_pairs if p['uop'] == 1], 'final reduction')
if final_red['result_hex'] != dot_pairs[0]['result_hex']:
    raise ValueError('Final baseline layout differs from vdot')
red_final_rename = require_one([e for e in reduce['renames'] if e['pdest'] == final_red['pdest']], 'final reduction rename')
if red_final_rename['ldest'] != 12:
    raise ValueError('Final reduction did not target architectural v12')
for instruction in (vadd, vdot):
    if len(instruction['renames']) != 1:
        raise ValueError('Expected single-uop target')
    execution = require_one([e for e in instruction['events'] if e['kind'] == 'exu_in'], 'accepted Exu input')
    if (execution['vsew'], execution['vlmul'], execution['vm'], execution['vstart']) != (0, 0, 1, 0):
        raise ValueError('Unexpected vector configuration')
    expected_vl = 16 if instruction is vadd else 8
    if execution['src4'] & 0xff != expected_vl:
        raise ValueError('Unexpected execution VL in VConfig')
summary = {
    'sampling': 'before rising backend clock edge; edge indices are capture-relative, not guest cycleCnt',
    'vadd_source': json.loads((args.vadd_events / 'metadata.json').read_text()),
    'latency_source': json.loads((args.latency_events / 'metadata.json').read_text()),
    'vadd_decode_attempt_edges': [e['edge'] for e in vadd_events if e['kind'] == 'decode' and e.get('pc') == vadd['pc']],
    'vadd': vadd, 'multiply': multiply, 'reduce': reduce, 'vdot': vdot,
    'fu_pairs': {'vadd': vadd_pairs, 'multiply': mul_pairs, 'reduce': red_pairs, 'vdot': dot_pairs},
    'baseline_input_to_final_result_cycles': final_red['output_edge'] - min(p['input_edge'] for p in mul_pairs),
    'vdot_input_to_result_cycles': dot_pairs[0]['cycles'],
    'boundary_note': 'Baseline includes intervening vector configurations, destination clearing and reduction scheduling. This is one traced combination, not steady-state throughput.'
}
(args.output / 'analysis.json').write_text(json.dumps(summary, indent=2) + '\n')
event_table(args.output / 'events.csv', {'vadd': vadd, 'vwmul': multiply, 'vwredsum': reduce, 'vdot': vdot})
vadd_rows = []
labels = {'decode': 'Decode', 'rename': 'Rename', 'issue': 'Issue',
          'fu_in': 'VialuFix input', 'fu_out': 'VialuFix output',
          'writeback': 'Writeback', 'preg_write': 'VF register write', 'commit': 'ROB commit'}
for kind, label in labels.items():
    event = require_one([e for e in vadd['events'] if e['kind'] == kind], label)
    vadd_rows.append((label, event['edge'], '#2563a6',
                      f'R=({vadd["rob_flag"]},{vadd["rob_value"]}), P={vadd_pairs[0]["pdest"]}'
                      if kind != 'decode' else f'PC {vadd["pc"]:#x}'))
diagram(args.output / 'vadd-timeline.svg', 'vadd.vv: committed instruction timeline', vadd_rows)
latency_rows = []
for name, ps, color in [('vwmul', mul_pairs, '#217a59'), ('vwredsum', red_pairs, '#217a59'), ('vdot', dot_pairs, '#a64b26')]:
    for pair in ps:
        for direction in ('input', 'output'):
            final_result = name == 'vdot' or (name == 'vwredsum' and pair['uop'] == 1)
            latency_rows.append((f'{name} uop {pair["uop"]} {direction}', pair[f'{direction}_edge'], color,
                                 f'P={pair["pdest"]}' + (', result=0x8 (128 bits)' if direction == 'output' and final_result else '')))
diagram(args.output / 'latency-timeline.svg', 'Equivalent baseline and vdot: arithmetic handshakes', latency_rows)
print(json.dumps({k: summary[k] for k in ('baseline_input_to_final_result_cycles', 'vdot_input_to_result_cycles')}))
