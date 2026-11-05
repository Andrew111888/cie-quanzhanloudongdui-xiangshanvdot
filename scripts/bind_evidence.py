"""Bind clean-checkout acceptance to an unchanged final implementation tree.

Report/demo additions after the tested commit are permitted and recorded;
processor, reference, workload, build configuration and harness inputs must be
byte-identical. Evidence retains both Git identities instead of inventing a
build under a later documentation-only commit.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('acceptance', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
directory = args.acceptance.resolve(strict=True)
acceptance = json.loads((directory / 'acceptance.json').read_text())
if acceptance['status'] != 'passed' or not acceptance['source_unchanged']:
    raise SystemExit('Acceptance is not complete')
if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=root, text=True):
    raise SystemExit('Commit the final source and documentation before binding')
args.output.parent.mkdir(parents=True, exist_ok=True)
current_path = args.output.with_suffix('.source.json')
subprocess.run([sys.executable, str(root / 'scripts/source_manifest.py'), str(current_path)], check=True)
current = json.loads(current_path.read_text())
tested = json.loads((directory / 'source-after.json').read_text())
if current['repositories'].keys() != tested['repositories'].keys():
    raise SystemExit('Upstream dependency coverage differs')


def submodule_identity(lines):
    result = {}
    for line in lines:
        match = re.fullmatch(r'([- +U])([0-9a-f]{40}) ([^ ]+)(?: \(.*\))?', line)
        if match is None:
            raise SystemExit('Unrecognized submodule identity record')
        state, digest, path = match.groups()
        if path in result or state in ('+', 'U'):
            raise SystemExit('Duplicate, conflicted or mismatched submodule: ' + path)
        result[path] = {'state': state, 'head': digest}
    return result


submodule_records = {}
for name, reference in tested['repositories'].items():
    actual = current['repositories'][name]
    for field in ('head', 'changed_source_sha256'):
        if actual[field] != reference[field]:
            raise SystemExit(f'Upstream source differs: {name}/{field}')
    expected_submodules = submodule_identity(reference['submodules'])
    actual_submodules = submodule_identity(actual['submodules'])
    if actual_submodules != expected_submodules:
        raise SystemExit('Submodule path, commit or initialization state differs: ' + name)
    submodule_records[name] = actual_submodules
prefixes = ('workloads/', 'datapath/', 'patches/', 'configs/', 'tests/')
required_scripts = {'scripts/build_emu.sh', 'scripts/build_nemu.sh', 'scripts/build_workloads.sh',
                    'scripts/build_fault_reference.sh', 'scripts/run_fault_check.sh',
                    'scripts/run_rtl.sh', 'scripts/env.sh', 'scripts/source_manifest.py',
                    'scripts/check_run.py', 'scripts/check_reference_abi.py',
                    'scripts/analyze_wave.py', 'scripts/analyze_pipeline_wave.py',
                    'scripts/extract_wave_events.py', 'scripts/performance_report.py',
                    'scripts/check_patches.py', 'scripts/lowmem-bin/mill',
                    'scripts/lowmem-bin/verilator'}
old = tested['project_files_sha256']
new = current['project_files_sha256']
critical = sorted(name for name in old.keys() | new.keys()
                  if name in ('contract.json', 'build.sc', 'build.mill')
                  or name.startswith(prefixes) or name in required_scripts)
for name in critical:
    if old.get(name) != new.get(name):
        raise SystemExit('Tested implementation/build/analysis input differs: ' + name)
run_records = {}
for name, run in acceptance['rtl_runs'].items():
    run = Path(run)
    if (run / 'exit-status.txt').read_text().strip() != '0':
        raise SystemExit('Invalid completed RTL result: ' + name)
    subprocess.run(['sha256sum', '--check', str(run / 'artifacts.sha256')],
                   check=True, stdout=subprocess.DEVNULL)
    run_records[name] = {'directory': str(run),
                         'log_sha256': hashlib.sha256((run / 'run.log').read_bytes()).hexdigest(),
                         'artifact_manifest_sha256': hashlib.sha256((run / 'artifacts.sha256').read_bytes()).hexdigest()}
if set(run_records) != {'vadd', 'smoke', 'register', 'random', 'pipeline', 'benchmark', 'latency'}:
    raise SystemExit('Required RTL run set is incomplete')
driver = Path(acceptance['driver'])
if hashlib.sha256(driver.read_bytes()).hexdigest() != acceptance['driver_sha256']:
    raise SystemExit('Acceptance driver changed after the recorded run')
non_dut_changes = sorted(name for name in old.keys() | new.keys()
                         if name not in critical and old.get(name) != new.get(name))
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
tree = subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=root, text=True).strip()
tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0')
tree_hashes = {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
               for name in tracked if name and (root / name).is_file()}
# Contact data is intentionally outside the source tree; never print its value.
contact = root / 'private/submission-contact.json'
if contact.exists():
    value = json.loads(contact.read_text())['contact_email'].encode()
    for name in tree_hashes:
        if value in (root / name).read_bytes():
            raise SystemExit('Private contact data appears in tracked file: ' + name)
result = {'status': 'verified', 'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
          'final_project_head': head, 'final_project_tree': tree,
          'tested_project_head': tested['project_head'], 'acceptance': str(directory),
          'acceptance_sha256': hashlib.sha256((directory / 'acceptance.json').read_bytes()).hexdigest(),
          'byte_identical_critical_inputs': critical, 'non_dut_changes_since_tested_checkout': non_dut_changes,
          'normalized_submodule_identity': submodule_records,
          'rtl_runs': run_records, 'tracked_file_sha256': tree_hashes,
          'note': 'This binds unchanged implementation bytes to a later documentation/tooling tree; it does not rename the original build commit.'}
args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print('FINAL_SOURCE_BINDING_VERIFIED', args.output)
