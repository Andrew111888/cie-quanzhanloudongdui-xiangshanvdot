"""Check shipped RTL, source snapshots, evidence hashes and documentation links."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def check(root):
    binding = read(root / 'experiments/acc/generated/provenance.json')
    rtl = read(root / 'rtl/provenance.json')
    assert rtl['build_status'] == 'completed'
    assert rtl['xiangshan_head'] == binding['core_commit']
    assert rtl['corrected_nemu_head'] == binding['corrected_reference_commit']
    modules = {item['file']: item for item in rtl['modules']}
    assert set(modules) == {'VdotAccRetimedDatapath.sv', 'VIMacU.sv'}
    for name, item in modules.items():
        assert digest(root / 'rtl' / name) == item['sha256'], name
        assert item['sha256'] == binding['files']['rtl/' + name]['sha256'], name
        assert (root / 'rtl' / name).read_bytes() == (root / item['verified_copy']).read_bytes(), name
    for name, item in binding['files'].items():
        assert digest(root / 'experiments/acc/generated' / name) == item['sha256'], name
    for name in ('xiangshan', 'nemu'):
        assert digest(root / 'patches' / (name + '.patch')) == rtl[name + '_patch_sha256'], name
    old = read(root / 'rtl/baseline/provenance.json')
    for item in old['modules']:
        assert digest(root / 'rtl/baseline' / item['file']) == item['sha256'], item['file']

    evidence_files = 0
    for directory in ('acc-results', 'acc-ppa', 'basic-current'):
        base = root / 'docs/data' / directory
        manifest = read(base / ('manifest.json' if directory == 'basic-current' else 'package-manifest.json'))
        for name, expected in manifest['files_sha256'].items():
            assert digest(base / name) == expected, str(base / name)
            evidence_files += 1
    validation = read(root / 'docs/data/acc-results/validation/results.json')
    benchmark = read(root / 'docs/data/acc-results/benchmark/results.json')
    precedence = read(root / 'docs/data/acc-results/precedence/results.json')
    assert validation['status'] == benchmark['status'] == precedence['status'] == 'passed'
    assert validation['scope'] == benchmark['scope'] == 'rtl_nemu_difftest'
    assert validation['random_input_groups'] == 1000 and validation['reported_core_dirty'] == 0
    assert benchmark['long_sample_count'] == 60 and benchmark['chain_sample_count'] == 120
    assert precedence['case_count'] == 48 and precedence['corrected_reference_rtl_all_cases_passed']
    basic = read(root / 'docs/data/basic-current/cases.json')
    basic_log = (root / 'docs/data/basic-current/run.log').read_text()
    assert basic['status'] == 'passed' and basic['source_unchanged'] and len(basic['cases']) == 6
    assert basic['difftest_enabled'] and basic['raw_exit_status'] == 0
    assert 'Difftest enabled.' in basic_log and 'HIT GOOD TRAP' in basic_log
    assert 'Commit SHA is: ' + binding['core_commit'][:10] + ', dirty: 0' in basic_log
    assert digest(root / 'rtl/VdotAccRetimedDatapath.sv') == digest(
        root / 'docs/data/acc-ppa/full-core/inputs/VdotAccRetimedDatapath.sv')

    documents = ['README.md', 'rtl/README.md', 'docs/SUBMISSION.md', 'docs/评审入口.md',
                 'docs/DESIGN.md', 'docs/BUILDING.md', 'docs/累加融合复现.md',
                 'docs/submission/stage1.md', 'docs/submission/stage2.md', 'docs/submission/stage3.md']
    for name in documents:
        path = root / name
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if '://' not in target and not target.startswith('#'):
                assert (path.parent / target.split('#')[0]).is_file(), (name, target)
    for path in (root / 'scripts').glob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
    return {'status': 'passed', 'current_rtl_modules': len(modules),
            'source_snapshot_files': len(binding['files']), 'verified_evidence_files': evidence_files,
            'random_input_groups': 1000, 'performance_samples': 180, 'cross_exception_cases': 48,
            'fresh_basic_cases': 6}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay-patches', action='store_true', help='Also compare pristine upstream patch replay with local sources')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = check(root)
    if args.replay_patches:
        subprocess.run(['python3', str(root / 'scripts/check_patches.py')], cwd=root, check=True)
        result['pristine_patch_replay'] = 'passed'
    print(json.dumps(result, ensure_ascii=False, indent=2))
