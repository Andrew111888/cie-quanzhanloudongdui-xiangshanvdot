"""Validate and map isolated fused-accumulator candidates under common constraints.

This experiment does not mutate accepted processor RTL. A fixed ABC target is
used once per design; both clock periods are checked on that identical netlist.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument('--yosys',type=Path,required=True)
parser.add_argument('--abc',type=Path,required=True)
parser.add_argument('--sta',type=Path,required=True)
parser.add_argument('--liberty',type=Path,required=True)
parser.add_argument('--verilator',type=Path,required=True)
parser.add_argument('--output',type=Path)
parser.add_argument('--chisel-plain',type=Path)
parser.add_argument('--chisel-csa',type=Path)
parser.add_argument('--chisel-prefix',type=Path)
parser.add_argument('--chisel-retimed',type=Path)
parser.add_argument('--designs',nargs='+')
args=parser.parse_args()
assert not args.chisel_retimed or args.chisel_plain, 'Generated retimed requires both other Chisel sources'
assert not args.chisel_prefix or args.chisel_plain, 'Generated prefix requires both other Chisel sources'
assert bool(args.chisel_plain)==bool(args.chisel_csa), 'Pass both generated Chisel sources or neither'
root=Path(__file__).resolve().parents[1]
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid())
report=(args.output or root/'reports'/('acc-ppa-'+stamp)).resolve()
evidence=report/'evidence';(evidence/'inputs').mkdir(parents=True,exist_ok=False)
commands=[]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(argv,log,cwd=root):
    argv=[str(x) for x in argv]
    commands.append({'argv':argv,'cwd':str(cwd),'log':str(log)})
    (evidence/'commands.json').write_text(json.dumps(commands,ensure_ascii=False,indent=2)+'\n')
    with log.open('w') as output:
        completed=subprocess.run(argv,cwd=cwd,stdout=output,stderr=subprocess.STDOUT)
    log.with_suffix(log.suffix+'.exit-status.txt').write_text(str(completed.returncode)+'\n')
    if completed.returncode:raise RuntimeError('Command failed: '+str(log))
    return log.read_text(errors='replace')
source_names=['rtl/VdotDatapath.sv','experiments/acc/VdotAccPlain.sv','experiments/acc/VdotAccCsa.sv',
              'experiments/acc/VdotAccCsaPrefix.sv','experiments/acc/VdotAccCsaPrefixOr.sv','experiments/acc/VdotAccRetimed.sv','experiments/acc/AccVerify.sv','verification/acc_arithmetic.cpp','scripts/evaluate_acc_ppa.py']
source_hashes={}
for name in source_names:
    path=root/name;source_hashes[name]=digest(path);shutil.copy2(path,evidence/'inputs'/path.name)
if args.chisel_plain:
    for path in ([args.chisel_plain,args.chisel_csa]+([args.chisel_prefix] if args.chisel_prefix else [])+([args.chisel_retimed] if args.chisel_retimed else [])):
        path=path.resolve(strict=True);source_hashes[str(path)]=digest(path);shutil.copy2(path,evidence/'inputs'/path.name)
    chisel_source=root/'third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala'
    source_hashes[str(chisel_source)]=digest(chisel_source);shutil.copy2(chisel_source,evidence/'inputs/Vdot.scala')
provenance=json.loads((root/'rtl/provenance.json').read_text())
assert any(m['file']=='VdotDatapath.sv' and m['sha256']==source_hashes['rtl/VdotDatapath.sv'] for m in provenance['modules'])
shutil.copy2(root/'docs/data/ppa/OpenCellLibraryLicenseSi2.txt',evidence/'inputs/OpenCellLibraryLicenseSi2.txt')
start_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
library_text=args.liberty.read_text()
assert digest(args.liberty)=='8d540a4d4cf6d09d27c87ad067857a9c0c2eeb023ab7a56e058cd3113db4e9b1'
for expression in (r'time_unit\s*:\s*"1ns"',r'capacitive_load_unit\s*\(\s*1\s*,\s*ff\s*\)',r'nom_voltage\s*:\s*1\.10',r'nom_temperature\s*:\s*25\.00'):
    assert re.search(expression,library_text)
library=evidence/'inputs/library-original.lib';shutil.copy2(args.liberty,library)
needle='default_wire_load : "5K_hvratio_1_1" ;'
zero_model=('wire_load("VDOT_ZERO_WIRE") { resistance : 0; capacitance : 0; '
            'area : 0; slope : 0; fanout_length(1,0); }\n'
            '  default_wire_load : "VDOT_ZERO_WIRE" ;')
assert library_text.count(needle)==1
zero_library=evidence/'inputs/library-zero-wire.lib';zero_library.write_text(library_text.replace(needle,zero_model))
(evidence/'library-derivation.json').write_text(json.dumps({'original_sha256':digest(library),'zero_wire_sha256':digest(zero_library),
    'only_replacement':{'before':needle,'after':zero_model},'cell_tables_modified':False,
    'source':'https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/6c6fc7e21b2d0b5b88b1a52d0a5860ea4d88e9e5/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib',
    'area_unit':'Liberty area attribute units'},indent=2)+'\n')
tools={}
for label,path,flags in [('yosys',args.yosys,['-V']),('abc',args.abc,['-c','version']),('sta',args.sta,['-version']),('verilator',args.verilator,['--version'])]:
    path=path.resolve(strict=True);version=run([path,*flags],evidence/(label+'-version.log')).strip()
    tools[label]={'path':str(path),'sha256':digest(path),'version':version}
(evidence/'toolchain.json').write_text(json.dumps(tools,indent=2)+'\n')
objects=report/'verification-objects'
verification_sources=([evidence/'inputs/VdotAccPlainDatapath.sv',evidence/'inputs/VdotAccCsaDatapath.sv'] if args.chisel_plain else [])
verification_defines=(['-DACC_WITH_CHISEL'] if args.chisel_plain else [])
if args.chisel_prefix:
    verification_sources.append(evidence/'inputs/VdotAccCsaPrefixDatapath.sv');verification_defines.append('-DACC_WITH_CHISEL_PREFIX')
if args.chisel_retimed:
    verification_sources.append(evidence/'inputs/VdotAccRetimedDatapath.sv');verification_defines.append('-DACC_WITH_CHISEL_RETIMED')
    # Full-core firtool removes the unused reset port; test elaboration retains it.
    if not re.search(r'input\s+(?:\[[^]]+\]\s+)?reset\b',args.chisel_retimed.read_text()):
        verification_defines.append('-DACC_CHISEL_RETIMED_NO_RESET')
run([args.verilator,'--cc','--exe','--top-module','AccVerify','-DSYNTHESIS','-Wno-fatal','--Mdir',objects,
     '-CFLAGS','-std=c++17 -O2',*verification_defines,*verification_sources,evidence/'inputs/VdotDatapath.sv',evidence/'inputs/VdotAccPlain.sv',
     evidence/'inputs/VdotAccCsa.sv',evidence/'inputs/VdotAccCsaPrefix.sv',evidence/'inputs/VdotAccCsaPrefixOr.sv',evidence/'inputs/VdotAccRetimed.sv',evidence/'inputs/AccVerify.sv',evidence/'inputs/acc_arithmetic.cpp'],evidence/'verification-generate.log')
run(['/usr/bin/make','-C',objects,'-f','VAccVerify.mk','-j','2','CXX=/usr/bin/g++','LINK=/usr/bin/g++','AR=/usr/bin/ar'],evidence/'verification-build.log')
verification=run([objects/'VAccVerify'],evidence/'verification.log')
pattern=r'ACC_ARITHMETIC_PASS directed=(\d+) random=(\d+) continuous_checked_each=(\d+) total_checked_each=(\d+) first_stage_captures=(\d+) result_captures=(\d+) enable1_hold_cycles=(\d+) enable2_hold_cycles=(\d+) result_bits=128 latency=2 initiation_interval=1 seed=20261106'
match=re.search(pattern,verification);assert match and int(match[2])>=1000 and int(match[7])>=100 and int(match[8])>=100
verification_record=dict(zip(('directed_cases','random_vectors','continuous_checked_each','total_checked_each','first_stage_captures','result_captures','enable1_hold_cycles','enable2_hold_cycles'),map(int,match.groups())))
verification_record.update(models_checked=['original','plain','csa','prefix','prefix_or','retimed']+(['chisel_plain','chisel_csa'] if args.chisel_plain else [])+(['chisel_prefix'] if args.chisel_prefix else [])+(['chisel_retimed'] if args.chisel_retimed else []),status='passed',result_bits=128,latency_cycles=2,initiation_interval_cycles=1,seed=20261106,scope='standalone arithmetic with independently controlled register enables')
(evidence/'verification.json').write_text(json.dumps(verification_record,indent=2)+'\n')
print('ACC_ARITHMETIC_VERIFIED '+str(evidence/'verification.json'),flush=True)

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


results=[]
designs=[('original','VdotDatapath.sv','VdotDatapath'),('plain','VdotAccPlain.sv','VdotAccPlain'),('csa','VdotAccCsa.sv','VdotAccCsa'),('prefix','VdotAccCsaPrefix.sv','VdotAccCsaPrefix'),('prefix_or','VdotAccCsaPrefixOr.sv','VdotAccCsaPrefixOr'),('retimed','VdotAccRetimed.sv','VdotAccRetimed')]
if args.chisel_plain:designs.extend([('chisel_plain','VdotAccPlainDatapath.sv','VdotAccPlainDatapath'),('chisel_csa','VdotAccCsaDatapath.sv','VdotAccCsaDatapath')])
if args.chisel_prefix:designs.append(('chisel_prefix','VdotAccCsaPrefixDatapath.sv','VdotAccCsaPrefixDatapath'))
if args.chisel_retimed:designs.append(('chisel_retimed','VdotAccRetimedDatapath.sv','VdotAccRetimedDatapath'))
if args.designs:
    assert set(args.designs)<=set(x[0] for x in designs)
    designs=[x for x in designs if x[0] in args.designs]
for design,filename,mod in designs:
    directory=evidence/design;directory.mkdir()
    wrapper=evidence/('inputs/PpaTop-'+design+'.sv')
    connections=('.clock(clock),.io_enable1(enable),.io_enable2(enable),.io_vs1(vs1),.io_vs2(vs2),.io_result(result)' if design=='original' else
                 '.clock(clock),.reset(1\'b0),.io_enable1(enable),.io_enable2(enable),.io_vs1(vs1),.io_vs2(vs2),.io_acc(acc),.io_result(result)' if design.startswith('chisel_') else
                 '.clock(clock),.enable1(enable),.enable2(enable),.vs1(vs1),.vs2(vs2),.acc(acc),.result(result)')
    if design=='chisel_retimed' and '-DACC_CHISEL_RETIMED_NO_RESET' in verification_defines:
        connections=connections.replace(".reset(1'b0),",'')
    wrapper.write_text('module PpaTop(input clock,input enable,input [127:0] vs1,input [127:0] vs2,input [31:0] acc,output [127:0] result);\n'+mod+' dut('+connections+');\nendmodule\n')
    script=directory/'synthesis.ys'
    script.write_text(f'''read_liberty -lib {library}
read_verilog -sv -DSYNTHESIS {evidence/'inputs'/filename} {wrapper}
hierarchy -top PpaTop
synth -top PpaTop -flatten -noabc
dffunmap
dfflibmap -liberty {library}
abc -exe {args.abc.resolve()} -liberty {library} -D 1000
delete t:$scopeinfo
clean
check -assert
stat -liberty {library}
write_json {directory/'mapped.json'}
write_verilog -noattr -simple-lhs {directory/'mapped.v'}
''')
    synthesis=run([args.yosys,'-Q','-s',script],directory/'synthesis.log')
    assert not re.search(r'^ERROR:|found and reported \d+ problems',synthesis,re.M)
    module=json.loads((directory/'mapped.json').read_text())['modules']['PpaTop']
    assert module['ports']['result']['bits'][32:]==['0']*96
    counts=Counter(cell['type'] for cell in module['cells'].values());assert all(name in lib_cells for name in counts)
    comb=sum(lib_cells[name]['area']*n for name,n in counts.items() if not lib_cells[name]['sequential'])
    seq=sum(lib_cells[name]['area']*n for name,n in counts.items() if lib_cells[name]['sequential'])
    area_line=re.search(r"Chip area for module '\\PpaTop': ([\d.]+)",synthesis);assert area_line and abs(float(area_line[1])-comb-seq)<1e-5
    timing_rows=[]
    for period in (1.0,1.5,2.5):
        label=str(period).replace('.','p');tcl=directory/('timing-'+label+'.tcl')
        tcl.write_text(f'''read_liberty {zero_library}
read_verilog {directory/'mapped.v'}
link_design PpaTop
set_units -time ns -capacitance fF
create_clock -name clk -period {period:.3f} [get_ports clock]
set_input_delay 0.100 -clock clk [get_ports {{enable vs1* vs2* acc*}}]
set_output_delay 0.100 -clock clk [get_ports result*]
set_input_transition 0.050 [get_ports {{enable vs1* vs2* acc*}}]
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
        timing=run([args.sta,'-exit',tcl],directory/('timing-'+label+'.log'));assert not re.search(r'^Error:',timing,re.M)
        check=timing.split('BEGIN_CHECK_SETUP\n',1)[1].split('END_CHECK_SETUP',1)[0]
        found=set(re.findall(r'^  (.+)$',check,re.M));expected={'result['+str(i)+']' for i in range(32,128)}
        assert found==expected and '96 unconstrained endpoints' in check
        setup=path_record(timing.split('BEGIN_SETUP_PATHS\n')[1].split('END_SETUP_PATHS')[0]);hold=path_record(timing.split('BEGIN_HOLD_PATHS\n')[1].split('END_HOLD_PATHS')[0])
        netlist=(directory/'mapped.v').read_text();setup['register_net_aliases']=register_aliases(netlist,setup);hold['register_net_aliases']=register_aliases(netlist,hold)
        wns=float(re.search(r'^worst slack ([\d.+-]+)',timing,re.M)[1]);tns=float(re.search(r'^tns ([\d.+-]+)',timing,re.M)[1])
        assert abs(wns-setup['slack_ns'])<1e-6
        timing_rows.append({'clock_period_ns':period,'worst_setup_slack_ns':wns,'total_negative_setup_slack_ns':tns,'setup_critical_path':setup,'hold_critical_path':hold,'constant_zero_outputs_without_timing_paths':96})
    entry={'design':design,'pipeline_stages':2,'accepted_input_interval_cycles':1,'sequential_cells':sum(n for name,n in counts.items() if lib_cells[name]['sequential']),
           'combinational_cells':sum(n for name,n in counts.items() if not lib_cells[name]['sequential']),'total_cells':sum(counts.values()),
           'combinational_area_library_units':round(comb,6),'sequential_area_library_units':round(seq,6),'total_area_library_units':round(comb+seq,6),
           'maximum_combinational_cell_levels':logic_depth(module),'mapped_netlist_sha256':digest(directory/'mapped.v'),'cell_type_counts':dict(sorted(counts.items())),
           'timing':timing_rows}
    (directory/'result.json').write_text(json.dumps(entry,indent=2)+'\n');results.append(entry)
    print('ACC_PPA_DESIGN_DONE '+design+' area='+str(entry['total_area_library_units'])+' wns='+','.join(str(x['worst_setup_slack_ns']) for x in timing_rows),flush=True)
assert all(digest(root/name)==value for name,value in source_hashes.items())
receipt={'status':'passed','source_head_at_start':start_head,'source_head_at_end':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
         'source_files_sha256':source_hashes,'selected_source_inputs_unchanged':True,'toolchain':tools,'verification':verification_record,
         'constraints':{'clock_periods_ns':[1.0,1.5,2.5],'clock_uncertainty_ns':.02,'input_delay_ns':.1,'output_delay_ns':.1,'input_transition_ns':.05,
                        'output_capacitance_fF':5.0,'interconnect_R_C':0,'clock_network':'ideal','corner':'Nangate45 typical 1.10V 25C',
                        'synthesis_abc_target_ps':1000,'mapping_policy':'one mapped netlist per design, unchanged for both STA clock periods',
                        'area_unit':'Liberty area attribute units'},'results':results,
         'scope':'isolated two-stage arithmetic only; acc selection mux, scheduler and processor integration excluded',
         'limitations':['No full-core area or power measurement','No physical placement, routing, parasitic extraction or CTS','A passing module constraint does not establish whole-chip frequency','Independent-enable arithmetic verification does not establish FU flush/ROB correctness']}
(evidence/'results.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
with (evidence/'summary.csv').open('w',newline='') as stream:
    writer=csv.writer(stream);writer.writerow(['design','total_area_library_units','sequential_cells','combinational_cells','max_logic_levels','wns_1ns','wns_1p5ns','wns_2p5ns','II','latency'])
    for x in results:writer.writerow([x['design'],x['total_area_library_units'],x['sequential_cells'],x['combinational_cells'],x['maximum_combinational_cell_levels'],*[t['worst_setup_slack_ns'] for t in x['timing']],1,2])
paths=sorted(p for p in evidence.rglob('*') if p.is_file())
(evidence/'SHA256SUMS').write_text(''.join(digest(p)+'  '+str(p.relative_to(evidence))+'\n' for p in paths))
print('ACC_PPA_EVALUATION_PASS '+str(evidence),flush=True)
