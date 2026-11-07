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
    basic_run = summary['stage2_basic']
    assert basic_run['status'] == 'passed' and basic_run['scope'] == 'rtl_nemu_difftest'
    assert basic_run['case_count'] == 6 and basic_run['raw_exit_status'] == 0
    assert basic_run['core_commit'] == manifest['tested']['XiangShan'] and basic_run['core_dirty'] == 0
    assert digest(root / basic_run['program']['file']) == basic_run['program']['sha256']
    terminal = basic_run['terminal_screenshot']
    assert terminal['displayed_cases_match_raw_log'] and terminal['case_count'] == 6
    assert terminal['test_exit_status'] == 0 and terminal['difftest_enabled']
    assert terminal['image_generation_used'] is False
    assert digest(root / terminal['file']) == terminal['sha256']
    wave = summary['current_vdot_waveform']
    assert wave['status'] == 'passed' and wave['core_dirty'] == 0
    assert wave['core_commit'] == manifest['tested']['XiangShan']
    assert wave['reference_commit'] == manifest['tested']['NEMU_corrected']
    assert wave['whole_core_rtl_byte_identical_to_performance_model']
    assert wave['performance_emulator_unchanged']
    assert digest(root / wave['probe_program']['file']) == wave['probe_program']['sha256']
    for name, expected in wave['analysis_scripts_sha256'].items():
        assert digest(root / name) == expected, name
    assert wave['rtl'] == manifest['rtl']
    probes = {p['instruction']: p for p in wave['probes']}
    assert set(probes) == {'vdot.vv', 'vdot.acc'}
    for name, expected in [('vdot.vv', 8), ('vdot.acc', 0x12345680)]:
        probe = probes[name]
        assert int(probe['result_hex'], 16) == expected
        assert probe['input_to_output_cycles'] == 2
        interfaces = probe['interfaces']
        assert interfaces['fu_output']['edge'] - interfaces['fu_input']['edge'] == 2
        assert interfaces['writeback']['edge'] == interfaces['physical_register_write']['edge'] == interfaces['fu_output']['edge']
        assert interfaces['commit']['edge'] >= interfaces['fu_output']['edge']
    assert int(probes['vdot.acc']['source_values_hex']['src2'], 16) & 0xffffffff == 0x12345678
    views = set()
    for screen in wave['screenshots']:
        assert screen['cursor_values_verified_from_raw_fst']
        assert digest(root / screen['file']) == screen['sha256'], screen['file']
        event = {'input': 'fu_input', 'output': 'fu_output', 'commit': 'commit'}[screen['view']]
        assert screen['marker_tick'] + 1 == probes[screen['instruction']]['interfaces'][event]['tick']
        views.add((screen['instruction'], screen['view']))
    assert len(wave['screenshots']) == len(views) == 6
    review = summary['stage3_review']
    assert review['status'] == 'passed'
    assert review['core_commit'] == manifest['tested']['XiangShan']
    assert review['reference_commit'] == manifest['tested']['NEMU_corrected']
    assert review['validation_shards_verified'] == 16 and review['benchmark_shards_verified'] == 8
    assert review['fault_exit_statuses'] == [0, 1, 0] and review['performance_samples'] == 180
    for source in ('baseline_program', 'nemu_patch'):
        assert digest(root / review[source]['file']) == review[source]['sha256']
    assert {s['view'] for s in review['terminal_screenshots']} == {'difftest', 'performance'}
    for screen in review['terminal_screenshots']:
        assert screen['visual_review'] == 'passed'
        assert digest(root / screen['file']) == screen['sha256']
    plot = review['plot']
    assert digest(root / plot['file']) == plot['sha256']
    for path, expected in plot['source_csvs'].items():
        assert digest(root / path) == expected
    paired = review['paired_baseline_waveform']
    assert paired['status'] == 'passed' and paired['core_dirty'] == 0
    assert paired['core_commit'] == manifest['tested']['XiangShan']
    assert paired['vdot_execution_cycles'] == 2 and paired['rvv_execution_span_cycles'] == 16
    assert paired['observed_span_ratio'] == paired['rvv_execution_span_cycles'] / paired['vdot_execution_cycles']
    assert int(paired['result_hex'], 16) == 131072
    assert paired['reduction_commit_debug_destination_is_internal_first_microop']
    assert digest(root / paired['program']['file']) == paired['program']['sha256']
    for name, expected in paired['analysis_scripts_sha256'].items():
        assert digest(root / name) == expected
    assert len(paired['screenshots']) == 2
    for screen in paired['screenshots']:
        assert screen['raw_fst_values_verified'] and screen['visual_review'] == 'passed'
        assert digest(root / screen['file']) == screen['sha256']
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
        if len(keys) == 2:
            for item in review['long_comparisons']:
                measured = {v: statistics.median(x[1] for x in groups[(v, item['k'])]) for v in range(4)}
                assert item['selected_rvv_median'] == min(measured[1], measured[2])
                assert abs(item['rvv_over_vdot'] - item['selected_rvv_median'] / measured[0]) < 1e-12
                assert abs(item['rvv_over_acc'] - item['selected_rvv_median'] / measured[3]) < 1e-12
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
            'random_input_groups': 1000, 'performance_samples': 180, 'exception_cases': 48,
            'current_waveform_probes': len(probes), 'current_waveform_screenshots': len(views)}


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
