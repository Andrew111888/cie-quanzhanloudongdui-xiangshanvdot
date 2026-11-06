"""Check the source distribution, published result tables and local links."""
import argparse
import ast
import csv
import hashlib
import json
from pathlib import Path
import re
import statistics
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(root):
    manifest = json.loads((root / 'configs/source-manifest.json').read_text())
    for group in ('patches', 'sources', 'rtl', 'baseline', 'comparison_rtl'):
        for name, expected in manifest[group].items():
            assert digest(root / name) == expected, name
    source_key = 'src/main/scala/xiangshan/backend/fu/vector/Vdot.scala'
    assert digest(root / 'src/Vdot.scala') == manifest['patched_sources']['XiangShan'][source_key]
    rtl = json.loads((root / 'rtl/provenance.json').read_text())
    assert rtl['build_status'] == 'completed' and rtl['xiangshan_head'] == manifest['tested']['XiangShan']
    for item in rtl['modules']:
        assert digest(root / 'rtl' / item['file']) == item['sha256'], item['file']

    summary = json.loads((root / 'docs/data/验证摘要.json').read_text())
    assert summary['status'] == 'passed' and summary['basic_cases'] == 6
    assert summary['core_commit'] == manifest['tested']['XiangShan']
    assert summary['random_input_groups'] == 1000 and summary['exception_cases'] == 48
    assert summary['fault_original_exit_codes'] == [0, 1, 0]
    for filename, count, keys, summaries in [
        ('长点积周期.csv', 60, ('variant', 'k'), summary['long_comparisons']),
        ('累加链周期.csv', 120, ('variant', 'chains', 'rounds'), summary['chain_comparisons']),
    ]:
        with (root / 'docs/data' / filename).open() as stream:
            rows = list(csv.DictReader(stream))
        assert len(rows) == count, filename
        groups = {}
        for row in rows:
            key = tuple(int(row[k]) for k in keys)
            groups.setdefault(key, []).append((int(row['repeat']), int(row['cycles'])))
        assert len(groups) == count // 5
        for values in groups.values():
            assert sorted(x[0] for x in values) == list(range(5)) and min(x[1] for x in values) > 0
        for item in summaries:
            if len(keys) == 2:
                measured = {v: statistics.median(x[1] for x in groups[(v, item['k'])]) for v in range(4)}
                assert measured[3] == item['acc_median']
                assert min(measured[1], measured[2]) == item['selected_rvv_median']
            else:
                measured = {v: statistics.median(x[1] for x in groups[(v, item['chains'], item['rounds'])]) for v in (0, 1)}
                assert measured[0] == item['dot_plus_add_median'] and measured[1] == item['acc_median']
    with (root / 'docs/data/基础测试.csv').open() as stream:
        basic = list(csv.DictReader(stream))
    assert len(basic) == 6
    for row in basic:
        expected = 8 * int(row['a']) * int(row['b'])
        assert int(row['expected']) == int(row['actual']) == expected
        assert int(row['vd_hex'], 16) == (expected & 0xffffffff)

    paths = [root / 'README.md', *(root / 'docs').rglob('*.md'), *(root / 'experiments').rglob('README.md'), *(root / 'rtl').rglob('README.md')]
    for path in paths:
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if '://' not in target and not target.startswith('#'):
                assert (path.parent / target.split('#')[0]).is_file(), (str(path.relative_to(root)), target)
    for path in (root / 'scripts').glob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
    return {'status': 'passed', 'rtl_modules': len(rtl['modules']), 'basic_cases': 6,
            'random_input_groups': 1000, 'performance_samples': 180, 'exception_cases': 48}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replay-patches', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = check(root)
    if args.replay_patches:
        subprocess.run(['python3', str(root / 'scripts/check_patches.py')], cwd=root, check=True)
        result['patch_replay'] = 'passed'
    print(json.dumps(result, ensure_ascii=False, indent=2))
