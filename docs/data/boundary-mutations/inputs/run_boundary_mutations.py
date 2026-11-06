"""Validate isolated mutations of the generated Vdot RTL with a full-width oracle."""
import argparse
from datetime import datetime, timezone
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--verilator', type=Path,
                    default=Path('/home/yh/chipyard/.conda-env/bin/verilator'))
parser.add_argument('--output', type=Path)
parser.add_argument('--jobs', type=int, default=2)
args = parser.parse_args()
assert 1 <= args.jobs <= 2
root = Path(__file__).resolve().parents[1]
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + str(os.getpid())
report = (args.output or root / 'reports' / ('boundary-mutations-' + stamp)).resolve()
report.mkdir(parents=True, exist_ok=False)
inputs = report / 'inputs'; inputs.mkdir()
evidence = report / 'evidence'; evidence.mkdir()
builds = report / 'builds'; builds.mkdir()
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
source = root / 'rtl/VdotDatapath.sv'
harness = root / 'verification/boundary_mutations.cpp'
provenance = root / 'rtl/provenance.json'
binding = json.loads(provenance.read_text())
module = next(item for item in binding['modules'] if item['file'] == source.name)
assert sha(source) == module['sha256'] and binding['build_status'] == 'completed'
original_sha = sha(source)
for path in (source, harness, provenance, Path(__file__).resolve()): shutil.copy2(path, inputs / path.name)
original = (inputs / source.name).read_text()
result_line = "      result <= {96'h0, {13{sum[18]}}, sum};"
sum_line = "  wire [18:0]  sum = 19'({quads_0[17], quads_0} + {quads_1[17], quads_1});"
assert original.count(result_line) == original.count(sum_line) == 1
variants = [
    ('normal', original, None, None),
    ('truncate_sum_18', original.replace(sum_line,
     "  wire [17:0]  sum = 18'({quads_0[17], quads_0} + {quads_1[17], quads_1});")
     .replace(result_line, "      result <= {96'h0, {14{sum[17]}}, sum};"),
     'boundary_min_min', '000000000000000000000000fffe0000'),
    ('zero_extend_negative', original.replace(result_line, "      result <= {96'h0, 13'h0, sum};"),
     'negative', '0000000000000000000000000007fff8'),
    ('corrupt_upper_zero', original.replace(result_line,
     "      result <= {96'h1, {13{sum[18]}}, sum};"),
     'positive', '00000000000000000000000100000008'),
    ('restored', original, None, None),
]
assert variants[0][1] == variants[-1][1]
commands = []

def run(argv, name, cwd=root, timeout=300):
    command = [str(part) for part in argv]
    commands.append({'name': name, 'argv': command, 'cwd': str(cwd)})
    (evidence / 'commands.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2) + '\n')
    with (evidence / (name + '.log')).open('w') as stream:
        started = time.monotonic()
        process = subprocess.run(['/usr/bin/time', '-v', '-o', str(evidence / (name + '-resources.txt')),
                                  *command], cwd=cwd, stdout=stream, stderr=stream, timeout=timeout)
    elapsed = time.monotonic() - started
    (evidence / (name + '-exit-status.txt')).write_text(str(process.returncode) + '\n')
    return process.returncode, elapsed

version = subprocess.check_output([str(args.verilator), '--version'], text=True).strip()
compiler = subprocess.check_output(['/usr/bin/g++', '--version'], text=True).splitlines()[0]
(evidence / 'tools.json').write_text(json.dumps({'verilator': version, 'verilator_path': str(args.verilator.resolve()),
    'verilator_driver_sha256': sha(args.verilator.resolve()), 'compiler': compiler,
    'compiler_path': '/usr/bin/g++', 'jobs': args.jobs}, ensure_ascii=False, indent=2) + '\n')
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
records = []
print('BOUNDARY_MUTATIONS_STARTED ' + str(report), flush=True)
for name, rtl, expected_case, expected_actual in variants:
    directory = builds / name; directory.mkdir()
    sv = directory / 'VdotDatapath.sv'; sv.write_text(rtl)
    shutil.copy2(inputs / 'boundary_mutations.cpp', directory / 'boundary_mutations.cpp')
    shutil.copy2(sv, evidence / (name + '.sv'))
    (evidence / (name + '.diff')).write_text(''.join(difflib.unified_diff(
        original.splitlines(True), rtl.splitlines(True), fromfile='original/VdotDatapath.sv',
        tofile=name + '/VdotDatapath.sv')))
    build_argv = [args.verilator, '--cc', '--exe', '--top-module', 'VdotDatapath',
                  '--Mdir', directory / 'obj_dir', '-O1', '-CFLAGS', '-std=c++17 -O2',
                  sv, directory / 'boundary_mutations.cpp']
    status, generate_seconds = run(build_argv, name + '-generate')
    assert status == 0, (name, 'model generation failure is not a detected RTL defect')
    status, seconds = run(['/usr/bin/make', '-C', directory / 'obj_dir', '-f', 'VVdotDatapath.mk',
                           '-j', str(args.jobs), 'CXX=/usr/bin/g++', 'LINK=/usr/bin/g++', 'AR=/usr/bin/ar'],
                          name + '-build')
    assert status == 0, (name, 'build failure is not a detected RTL defect')
    executable = directory / 'obj_dir/VVdotDatapath'; assert executable.is_file()
    status, run_seconds = run([executable], name + '-run', timeout=30)
    output = (evidence / (name + '-run.log')).read_text()
    if expected_case is None:
        assert status == 0 and 'VDOT_RTL_PASS directed_cases=6 random_cases=1000 seed=20261106' in output
        assert output.count('RTL_CASE_PASS ') == 6 and 'RTL_MISMATCH' not in output
        outcome = 'passed'
        mismatch = None
    else:
        assert status == 42 and 'VDOT_RTL_PASS' not in output
        mismatch = re.search(r'^RTL_MISMATCH name=(\w+) phase=(\w+) cycle=(\d+) signed_expected=(-?\d+) '
                            r'expected128=([0-9a-f]{32}) actual128=([0-9a-f]{32})$', output, re.M)
        assert mismatch and mismatch[1] == expected_case and mismatch[6] == expected_actual
        assert mismatch[5] != mismatch[6]
        mismatch = {'case': mismatch[1], 'phase': mismatch[2], 'cycle': int(mismatch[3]),
                    'signed_expected': int(mismatch[4]), 'expected128': mismatch[5], 'actual128': mismatch[6]}
        outcome = 'detected_by_result_assertion'
    records.append({'variant': name, 'status': outcome, 'rtl_sha256': sha(sv),
                    'executable_sha256': sha(executable), 'build_exit_status': 0,
                    'run_exit_status': status, 'mismatch': mismatch,
                    'model_generation_elapsed_seconds': round(generate_seconds, 6),
                    'build_elapsed_seconds': round(seconds, 6), 'run_elapsed_seconds': round(run_seconds, 6),
                    'run_log_sha256': sha(evidence / (name + '-run.log'))})
    print('BOUNDARY_VARIANT ' + name + ' ' + outcome, flush=True)
assert sha(source) == original_sha
assert sha(harness) == sha(inputs / harness.name)
assert records[0]['rtl_sha256'] == records[-1]['rtl_sha256'] == original_sha
input_hashes = {str(path.relative_to(report)): sha(path) for path in inputs.iterdir()}
evidence_hashes = {str(path.relative_to(report)): sha(path) for path in evidence.iterdir() if path.is_file()}
result = {'schema': 'vdot-boundary-mutations/v1', 'status': 'passed',
    'source_project_head_at_start': head,
    'source_project_head_at_end': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
    'input_files_unchanged': True, 'original_generated_rtl_sha256': original_sha,
    'generated_rtl_binding': binding, 'seed': 20261106, 'directed_cases_per_positive_run': 6,
    'random_cases_per_positive_run': 1000, 'enable_stress_cycles_per_positive_run': 1006,
    'mutation_count': 3, 'mutations_detected': 3, 'normal_passed': True, 'restored_passed': True,
    'result_comparison_bits': 128, 'records': records, 'tools': json.loads((evidence / 'tools.json').read_text()),
    'input_sha256': input_hashes, 'evidence_sha256': evidence_hashes,
    'scope': 'Standalone simulation of the generated two-stage RTL datapath and isolated RTL mutations; full-core RTL/NEMU evidence remains separate.',
    'frozen_rtl_or_patch_modified': False, 'elapsed_seconds': round(sum(r['model_generation_elapsed_seconds'] + r['build_elapsed_seconds'] + r['run_elapsed_seconds'] for r in records), 6)}
(report / 'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print('BOUNDARY_MUTATIONS_PASS ' + str(report), flush=True)
