"""Compare isolated two/four-stage dot-product datapaths under one public library.

The accepted XiangShan implementation is read-only. Results describe mapped
module cells and pre-layout STA; they are not full-core area, power or frequency.
"""
import argparse
from collections import Counter
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
parser.add_argument('--yosys', type=Path, required=True)
parser.add_argument('--abc', type=Path, required=True)
parser.add_argument('--sta', type=Path, required=True)
parser.add_argument('--liberty', type=Path, required=True)
parser.add_argument('--verilator', type=Path, required=True)
parser.add_argument('--output', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + str(os.getpid())
report = (args.output or root / 'reports' / ('ppa-' + stamp)).resolve()
evidence = report / 'evidence'
(evidence / 'inputs').mkdir(parents=True, exist_ok=False)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


commands = []


def run(command, log, cwd=root):
    command = [str(item) for item in command]
    commands.append({'argv': command, 'cwd': str(cwd), 'log': str(log)})
    (evidence / 'commands.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2) + '\n')
    with log.open('w') as stream:
        completed = subprocess.run(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT)
    log.with_suffix(log.suffix + '.exit-status.txt').write_text(str(completed.returncode) + '\n')
    if completed.returncode:
        raise RuntimeError('Command failed: ' + str(log))
    return log.read_text(errors='replace')


source_names = ['rtl/baseline/VdotDatapath.sv', 'experiments/ppa/VdotPipelined4.sv',
                'experiments/ppa/PpaTop2.sv', 'experiments/ppa/PpaTop4.sv',
                'experiments/ppa/PpaVerify.sv', 'experiments/ppa/verify.cpp',
                'scripts/evaluate_datapath_ppa.py']
source_hashes = {}
for name in source_names:
    path = root / name
    source_hashes[name] = digest(path)
    shutil.copy2(path, evidence / 'inputs' / path.name)
provenance = json.loads((root / 'rtl/baseline/provenance.json').read_text())
assert any(module['file'] == 'VdotDatapath.sv' and module['sha256'] == source_hashes['rtl/baseline/VdotDatapath.sv']
           for module in provenance['modules'])
library_text = args.liberty.read_text()
assert re.search(r'time_unit\s*:\s*"1ns"', library_text)
assert re.search(r'capacitive_load_unit\s*\(\s*1\s*,\s*ff\s*\)', library_text)
assert re.search(r'nom_voltage\s*:\s*1\.10', library_text)
assert re.search(r'nom_temperature\s*:\s*25\.00', library_text)
library = evidence / 'inputs/library-original.lib'
shutil.copy2(args.liberty, library)
needle = 'default_wire_load : "5K_hvratio_1_1" ;'
assert library_text.count(needle) == 1
zero_model = ('wire_load("VDOT_ZERO_WIRE") { resistance : 0; capacitance : 0; '
              'area : 0; slope : 0; fanout_length(1,0); }\n'
              '  default_wire_load : "VDOT_ZERO_WIRE" ;')
zero_library = evidence / 'inputs/library-zero-wire.lib'
zero_library.write_text(library_text.replace(needle, zero_model))
(evidence / 'library-derivation.json').write_text(json.dumps({
    'source': 'https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/6c6fc7e21b2d0b5b88b1a52d0a5860ea4d88e9e5/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib',
    'original_sha256': digest(library), 'zero_wire_sha256': digest(zero_library),
    'only_replacement': {'before': needle, 'after': zero_model},
    'cell_tables_modified': False, 'purpose': 'Explicit zero interconnect R/C in both STA experiments',
    'time_unit': 'ns', 'capacitance_unit': 'fF', 'area_unit': 'Liberty area attribute units',
    'nominal_voltage_V': 1.10, 'nominal_temperature_C': 25.0,
}, ensure_ascii=False, indent=2) + '\n')

tools = {}
for label, path, flags in [('yosys', args.yosys, ['-V']), ('abc', args.abc, ['-c', 'version']),
                           ('sta', args.sta, ['-version']), ('verilator', args.verilator, ['--version'])]:
    path = path.resolve(strict=True)
    version = run([path, *flags], evidence / (label + '-version.log')).strip()
    tools[label] = {'path': str(path), 'sha256': digest(path), 'version': version}
(evidence / 'toolchain.json').write_text(json.dumps(tools, indent=2) + '\n')

obj = report / 'verification-objects'
run([args.verilator.resolve(), '--cc', '--exe', '--build', '-j', '2', '--top-module', 'PpaVerify',
     '-DSYNTHESIS', '-Wno-fatal', '--Mdir', obj, evidence / 'inputs/VdotDatapath.sv',
     evidence / 'inputs/VdotPipelined4.sv', evidence / 'inputs/PpaVerify.sv', evidence / 'inputs/verify.cpp'],
    evidence / 'verification-build.log')
verification = run([obj / 'VPpaVerify'], evidence / 'verification.log')
match = re.search(r'PPA_ARITHMETIC_PASS accepted=(\d+) stalls=(\d+) checked_two_stage=(\d+) checked_four_stage=(\d+) latency2=2 latency4=4 initiation_interval_both=1 seed=20261106', verification)
assert match and int(match[1]) >= 1000 and int(match[2]) >= 100


def blocks(text, expression):
    for match in re.finditer(expression, text):
        opening = text.index('{', match.start())
        depth = 1; ending = opening + 1
        while depth:
            depth += (text[ending] == '{') - (text[ending] == '}'); ending += 1
        yield match[1], text[opening + 1:ending - 1]


lib_cells = {}
for name, body in blocks(library_text, r'\bcell\s*\(\s*([^\s)]+)\s*\)\s*\{'):
    area = float(re.search(r'\barea\s*:\s*([\d.eE+-]+)', body)[1])
    sequential = bool(re.search(r'\b(?:ff|latch)\s*\(', body))
    lib_cells[name] = {'area': area, 'sequential': sequential}


def logic_depth(module):
    # Logical cell levels count each mapped combinational cell once. This is
    # independent of the Liberty delay and has no physical time unit.
    depth = {str(bit): 0 for port in module['ports'].values() if port['direction'] == 'input' for bit in port['bits']}
    depth.update({'0': 0, '1': 0, 'x': 0, 'z': 0})
    pending = []
    for cell in module['cells'].values():
        if lib_cells[cell['type']]['sequential']:
            for name, bits in cell['connections'].items():
                if cell['port_directions'][name] == 'output':
                    depth.update({str(bit): 0 for bit in bits})
        else:
            pending.append(cell)
    while pending:
        remaining = []
        for cell in pending:
            inputs = [str(bit) for name, bits in cell['connections'].items()
                      if cell['port_directions'][name] == 'input' for bit in bits]
            if all(bit in depth for bit in inputs):
                level = 1 + max((depth[bit] for bit in inputs), default=0)
                for name, bits in cell['connections'].items():
                    if cell['port_directions'][name] == 'output':
                        depth.update({str(bit): level for bit in bits})
            else: remaining.append(cell)
        if len(remaining) == len(pending): raise RuntimeError('Unresolved combinational cycle or cell direction')
        pending = remaining
    endpoints = [str(bit) for port in module['ports'].values() if port['direction'] == 'output' for bit in port['bits']]
    for cell in module['cells'].values():
        if lib_cells[cell['type']]['sequential']:
            endpoints.extend(str(bit) for name, bits in cell['connections'].items()
                             if cell['port_directions'][name] == 'input' and name != 'CK' for bit in bits)
    return max(depth[bit] for bit in endpoints)


def path_record(text):
    start = re.search(r'^Startpoint: (.+)$', text, re.M)
    end = re.search(r'^Endpoint: (.+)$', text, re.M)
    arrival = re.search(r'^\s*([\d.+-]+)\s+data arrival time$', text, re.M)
    required = re.search(r'^\s*([\d.+-]+)\s+data required time$', text, re.M)
    slack = re.search(r'^\s*([\d.+-]+)\s+slack \((?:MET|VIOLATED)\)', text, re.M)
    assert start and end and arrival and required and slack
    return {'startpoint': start[1], 'endpoint': end[1], 'data_arrival_ns': float(arrival[1]),
            'data_required_ns': float(required[1]), 'slack_ns': float(slack[1])}


def register_aliases(netlist, path):
    aliases = {}
    for role in ('startpoint', 'endpoint'):
        instance = path[role].split(' ', 1)[0]
        cell = re.search(r'\bDFF_X1\s+' + re.escape(instance) + r'\s*\((.*?)\n\s*\);', netlist, re.S)
        if cell is None:
            aliases[role] = [instance]
            continue
        output = re.search(r'\.Q\(([^)]+)\)', cell[1])
        assert output
        aliases[role] = [output[1].replace('\\', '').replace(' ', '')]
    return aliases


results = []
for stages in (2, 4):
    directory = evidence / ('stages' + str(stages)); directory.mkdir()
    source = evidence / ('inputs/' + ('VdotDatapath.sv' if stages == 2 else 'VdotPipelined4.sv'))
    script = directory / 'synthesis.ys'
    script.write_text(f'''read_liberty -lib {library}
read_verilog -sv -DSYNTHESIS {source} {evidence / ('inputs/PpaTop' + str(stages) + '.sv')}
hierarchy -top PpaTop
synth -top PpaTop -flatten -noabc
dffunmap
dfflibmap -liberty {library}
abc -exe {args.abc.resolve()} -liberty {library} -D 1000
delete t:$scopeinfo
clean
check -assert
stat -liberty {library}
write_json {directory / 'mapped.json'}
write_verilog -noattr {directory / 'mapped.v'}
''')
    synthesis = run([args.yosys.resolve(), '-Q', '-s', script], directory / 'synthesis.log')
    assert not re.search(r'^ERROR:|found and reported \d+ problems', synthesis, re.M)
    module = json.loads((directory / 'mapped.json').read_text())['modules']['PpaTop']
    assert module['ports']['result']['bits'][32:] == ['0'] * 96
    counts = Counter(cell['type'] for cell in module['cells'].values())
    assert all(name in lib_cells for name in counts)
    comb = sum(lib_cells[name]['area'] * n for name, n in counts.items() if not lib_cells[name]['sequential'])
    seq = sum(lib_cells[name]['area'] * n for name, n in counts.items() if lib_cells[name]['sequential'])
    total = comb + seq
    area_line = re.search(r"Chip area for module '\\PpaTop': ([\d.]+)", synthesis)
    assert area_line and abs(float(area_line[1]) - total) < 1e-5
    tcl = directory / 'timing.tcl'
    tcl.write_text(f'''read_liberty {zero_library}
read_verilog {directory / 'mapped.v'}
link_design PpaTop
set_units -time ns -capacitance fF
create_clock -name clk -period 1.000 [get_ports clock]
set_input_delay 0.100 -clock clk [get_ports {{enable vs1* vs2*}}]
set_output_delay 0.100 -clock clk [get_ports result*]
set_input_transition 0.050 [get_ports {{enable vs1* vs2*}}]
set_load 5.000 [get_ports result*]
set_clock_uncertainty 0.020 [get_clocks clk]
set_wire_load_model -name VDOT_ZERO_WIRE
puts "BEGIN_CHECK_SETUP"
check_setup -verbose
puts "END_CHECK_SETUP"
puts "BEGIN_SETUP_PATHS"
report_checks -path_delay max -group_count 3 -sort_by_slack -fields {{slew capacitance input_pin net}} -digits 6
puts "END_SETUP_PATHS"
puts "BEGIN_HOLD_PATHS"
report_checks -path_delay min -group_count 3 -sort_by_slack -fields {{slew capacitance input_pin net}} -digits 6
puts "END_HOLD_PATHS"
report_worst_slack -digits 6
report_check_types -min_delay -all_violators -digits 6
report_clock_properties
report_tns -digits 6
exit
''')
    timing = run([args.sta.resolve(), '-exit', tcl], directory / 'timing.log')
    assert not re.search(r'^Error:', timing, re.M), str(tcl)
    check = timing.split('BEGIN_CHECK_SETUP\n', 1)[1].split('END_CHECK_SETUP', 1)[0]
    expected = {'result[' + str(i) + ']' for i in range(32, 128)}
    found = set(re.findall(r'^  (.+)$', check, re.M))
    assert found == expected and '96 unconstrained endpoints' in check
    setup = path_record(timing.split('BEGIN_SETUP_PATHS\n')[1].split('END_SETUP_PATHS')[0])
    hold = path_record(timing.split('BEGIN_HOLD_PATHS\n')[1].split('END_HOLD_PATHS')[0])
    setup['register_net_aliases'] = register_aliases((directory / 'mapped.v').read_text(), setup)
    hold['register_net_aliases'] = register_aliases((directory / 'mapped.v').read_text(), hold)
    wns = float(re.search(r'^worst slack ([\d.+-]+)', timing, re.M)[1])
    tns = float(re.search(r'^tns ([\d.+-]+)', timing, re.M)[1])
    assert abs(wns - setup['slack_ns']) < 1e-6
    result = {'pipeline_stages': stages, 'accepted_input_interval_cycles': 1,
              'sequential_cells': sum(n for name, n in counts.items() if lib_cells[name]['sequential']),
              'combinational_cells': sum(n for name, n in counts.items() if not lib_cells[name]['sequential']),
              'total_cells': sum(counts.values()), 'combinational_area_library_units': round(comb, 6),
              'sequential_area_library_units': round(seq, 6), 'total_area_library_units': round(total, 6),
              'maximum_combinational_cell_levels': logic_depth(module),
              'setup_critical_path': setup, 'hold_critical_path': hold,
              'worst_setup_slack_ns': wns, 'total_negative_setup_slack_ns': tns,
              'constant_zero_outputs_without_timing_paths': 96,
              'mapped_netlist_sha256': digest(directory / 'mapped.v'), 'cell_type_counts': dict(sorted(counts.items()))}
    (directory / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    results.append(result)

assert all(digest(root / name) == value for name, value in source_hashes.items())
receipt = {'status': 'passed', 'source_project_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
           'source_files_sha256': source_hashes, 'toolchain': tools,
           'verification': {'accepted_vectors': int(match[1]), 'clock_enable_stalls': int(match[2]),
                            'two_stage_checked_results': int(match[3]), 'four_stage_checked_results': int(match[4]),
                            'fixed_seed': 20261106, 'directed_cases': 6,
                            'two_stage_latency_enabled_edges': 2, 'four_stage_latency_enabled_edges': 4,
                            'initiation_interval_enabled_edges_both': 1, 'scope': 'standalone arithmetic and common-enable stall behavior'},
           'constraints': {'clock_period_ns': 1.0, 'clock_uncertainty_ns': 0.02, 'input_delay_ns': 0.1,
                           'output_delay_ns': 0.1, 'input_transition_ns': 0.05, 'output_capacitance_fF': 5.0,
                           'interconnect_R_C': 0, 'clock_network': 'ideal', 'corner': 'Nangate45 typical 1.10V 25C',
                           'synthesis_abc_target_ps': 1000, 'area_unit': 'Liberty area attribute units'},
           'results': results, 'scope': 'isolated Vdot arithmetic, two versus four stages; original XiangShan sources unchanged',
           'limitations': ['No full-core area or power measurement', 'No placement, routing, extracted parasitics or clock-tree synthesis',
                           'Four-stage design is an isolated prototype and does not implement FU valid/ROB/flush integration',
                           'Raw nonpositive setup slack at the fixed 1ns constraint must not be reported as achieved chip frequency'],
           'final_source_files_unchanged': True}
(evidence / 'results.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
files = sorted(p for p in evidence.rglob('*') if p.is_file())
(evidence / 'SHA256SUMS').write_text(''.join(digest(p) + '  ' + str(p.relative_to(evidence)) + '\n' for p in files))
print('PPA_EVALUATION_PASS ' + str(evidence), flush=True)
print(json.dumps({'verification': receipt['verification'], 'results': results}, ensure_ascii=False), flush=True)
