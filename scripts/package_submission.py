"""Build the four official upload categories from verified final artifacts.

Raw environment logs/FST stay in the judge-facing evidence ZIP. The public
source archive uses only Git-tracked files; private submission contact data is
never included in any package.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--binding', type=Path, required=True)
parser.add_argument('--pdf-dir', type=Path, help='Directory containing final PDFs and reports-manifest.json')
parser.add_argument('--submission-checklist', type=Path, help='Reviewed requirement mapping to include in every archive')
parser.add_argument('--workflow-receipt', type=Path, help='Current external submission metadata to include in every archive')
parser.add_argument('--pristine-run', type=Path, help='Explicit historical unmodified-core vadd evidence')
parser.add_argument('--optimization-dir', type=Path, help='Verified before/after RTL performance report')
parser.add_argument('--reproduction-status', type=Path, help='Completed clean source reproduction status')
parser.add_argument('--stage1-video', type=Path, required=True)
parser.add_argument('--stage2-video', type=Path, required=True)
parser.add_argument('--stage3-video', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
binding_path = args.binding.resolve(strict=True)
binding = json.loads(binding_path.read_text())
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
if binding['status'] != 'verified' or binding['final_project_head'] != head:
    raise SystemExit('Final source binding is missing or stale')
for name, expected in binding['tracked_file_sha256'].items():
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
        raise SystemExit('Tracked input changed after binding: ' + name)
acceptance_path = Path(binding['acceptance'])
acceptance = json.loads((acceptance_path / 'acceptance.json').read_text())
if acceptance['status'] != 'passed':
    raise SystemExit('Full clean-checkout acceptance did not pass')
pdf_path = args.pdf_dir.resolve(strict=True) if args.pdf_dir else root / 'output/pdf-release'
pdf_manifest = json.loads((pdf_path / 'reports-manifest.json').read_text())
if pdf_manifest['status'] != 'final' or pdf_manifest['final_project_head'] != head:
    raise SystemExit('Final PDFs are missing or bound to another source commit')
if pdf_manifest['binding_sha256'] != hashlib.sha256(binding_path.read_bytes()).hexdigest():
    raise SystemExit('PDF source binding differs')
videos = []
for stage, path in enumerate((args.stage1_video, args.stage2_video, args.stage3_video), 1):
    path = path.resolve(strict=True)
    meta = json.loads((path / 'recording.json').read_text())
    script = root / f'scripts/demo_stage{stage}.sh'
    if not meta['recording_complete'] or meta['command_exit_status'] != 0:
        raise SystemExit(f'Stage {stage} recording did not complete')
    if meta['script_sha256'] != hashlib.sha256(script.read_bytes()).hexdigest():
        raise SystemExit(f'Stage {stage} recording script changed')
    if float(meta['video']['format']['duration']) < 10:
        raise SystemExit(f'Stage {stage} recording is unexpectedly short')
    if meta['video_sha256'] != hashlib.sha256((path / 'recording.mp4').read_bytes()).hexdigest():
        raise SystemExit(f'Stage {stage} video digest changed')
    videos.append(path)
if len({p.resolve() for p in videos}) != 3:
    raise SystemExit('The three videos must be different real sessions')
destination = args.output.resolve()
destination.mkdir(parents=True, exist_ok=False)
readme = ('香山向量点积指令设计 - 全栈漏洞队\n'
          f'最终作品源码：{head}\n实际干净构建源码：{binding["tested_project_head"]}\n'
          '作品仓库：https://github.com/Andrew111888/cie-quanzhanloudongdui-xiangshanvdot\n'
          '核心代码、工作负载、配置和分析输入已逐字节绑定；后续文档/演示工具差异见source-binding.json。\n'
          '语义未明确事项已向官方Issue #126询问；当前契约仍为暂定解释，详见源码docs/QUESTIONS.md。\n'
          '延迟、吞吐与程序片段加速比分别说明；没有面积、频率、功耗或能效实测声明。\n'
          '原始环境输出及FST仅放在相关证明材料包，不进入公有源码包。\n')


def digest_file(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def archive(name, files, extra=None):
    files = dict(files)
    extra = {'README.txt': readme, **(extra or {})}
    if args.submission_checklist:
        extra['SUBMISSION_CHECKLIST.md'] = args.submission_checklist.read_text()
    if args.workflow_receipt:
        extra['workflow-receipt.json'] = args.workflow_receipt.read_text()
    if len(files) != len(set(files)) or files.keys() & extra.keys():
        raise ValueError('Duplicate ZIP entry')
    manifest = []
    target = destination / name
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for relative, path in sorted(files.items()):
            if relative.startswith('/') or '..' in Path(relative).parts:
                raise ValueError('Unsafe ZIP entry: ' + relative)
            output.write(path, relative)
            manifest.append(digest_file(path) + '  ' + relative)
        for relative, value in sorted(extra.items()):
            output.writestr(relative, value)
            manifest.append(hashlib.sha256(value.encode()).hexdigest() + '  ' + relative)
        output.writestr('CONTENTS.sha256', '\n'.join(manifest) + '\n')
    if target.stat().st_size >= 450_000_000:
        raise SystemExit('ZIP exceeds the internal 450MB limit: ' + name)
    with zipfile.ZipFile(target) as check:
        if check.testzip() is not None:
            raise SystemExit('ZIP integrity check failed: ' + name)
    return {'file': str(target), 'bytes': target.stat().st_size, 'sha256': digest_file(target)}


pdfs = {}
for item in pdf_manifest['reports']:
    path = Path(item['file'])
    if digest_file(path) != item['sha256']:
        raise SystemExit('Final PDF changed: ' + path.name)
    pdfs['documents/' + path.name] = path
pdfs['source-binding.json'] = binding_path
pdfs['reports-manifest.json'] = pdf_path / 'reports-manifest.json'
if (pdf_path / 'pdf-metadata-cleaning.json').exists():
    pdfs['pdf-metadata-cleaning.json'] = pdf_path / 'pdf-metadata-cleaning.json'
video_files = {}
for stage, path in enumerate(videos, 1):
    for name in ('recording.mp4', 'recording.json', 'commands.sh', 'terminal.log', 'terminal.timing',
                 'source-before.json', 'source-after.json', 'ffmpeg.log', 'xterm.log', 'xvfb.log'):
        video_files[f'stage{stage}/' + name] = path / name
video_files['source-binding.json'] = binding_path
video_quality = videos[0].parent / 'quality-check.json'
if all(path.parent == videos[0].parent for path in videos) and video_quality.exists():
    video_files['video-quality-check.json'] = video_quality
evidence = {'source-binding.json': binding_path}
for name, run in acceptance['rtl_runs'].items():
    folder = Path(run)
    for path in folder.rglob('*'):
        if path.is_file():
            evidence['rtl/' + name + '/' + str(path.relative_to(folder))] = path
for path in acceptance_path.rglob('*'):
    if path.is_file():
        evidence['acceptance/' + str(path.relative_to(acceptance_path))] = path
diagnostic_log = acceptance_path / 'pipeline-diagnostic.log'
diagnostic_folders = [Path(line.removeprefix('RTL evidence: '))
                      for line in diagnostic_log.read_text().splitlines()
                      if line.startswith('RTL evidence: ')]
if len(diagnostic_folders) != 1:
    raise SystemExit('Missing exact pipeline diagnostic run')
diagnostic = diagnostic_folders[0]
purpose = json.loads((diagnostic / 'diagnostic-purpose.json').read_text())
pipeline_analysis = json.loads((acceptance_path / 'pipeline-analysis/pipeline-analysis.json').read_text())
if purpose['functional_pass'] or purpose['expected_budget_stop'] != 28000:
    raise SystemExit('Pipeline diagnostic was incorrectly classified as a functional pass')
if digest_file(diagnostic / 'wave.fst') != pipeline_analysis['metadata']['fst_sha256']:
    raise SystemExit('Raw pipeline diagnostic FST differs from its analyzed source')
for path in diagnostic.rglob('*'):
    if path.is_file():
        evidence['diagnostic/pipeline/' + str(path.relative_to(diagnostic))] = path
fault_outer = next((line.removeprefix('Fault-check evidence: ') for line in
                    (acceptance_path / 'fault-check.log').read_text().splitlines()
                    if line.startswith('Fault-check evidence: ')), None)
if fault_outer is None:
    raise SystemExit('Missing fault injection evidence directory')
fault_outer = Path(fault_outer)
for path in fault_outer.rglob('*'):
    if path.is_file(): evidence['fault-check/' + str(path.relative_to(fault_outer))] = path
negative = json.loads((fault_outer / 'detected-mismatch.json').read_text())
for label in ('positive-before', 'negative', 'positive-restored'):
    lines = (fault_outer / (label + '.log')).read_text().splitlines()
    directory = Path(next(s.removeprefix('RTL evidence: ') for s in lines if s.startswith('RTL evidence: ')))
    for path in directory.rglob('*'):
        if path.is_file(): evidence['fault-runs/' + label + '/' + str(path.relative_to(directory))] = path
tested_root = acceptance_path.parents[1]
for name in ('pristine-preserved.sha256', 'pristine-sources.json', 'pristine-vadd-evidence.txt', 'toolchain-identity.json', 'host-environment.json'):
    path = tested_root / 'reports' / name
    if path.exists(): evidence['pristine/' + name] = path
pristine_run = (args.pristine_run.resolve(strict=True) if args.pristine_run else
                Path((tested_root / 'reports/pristine-vadd-evidence.txt').read_text().strip()))
if (pristine_run / 'exit-status.txt').read_text().strip() != '0':
    raise SystemExit('Historical unmodified-core vadd evidence did not pass')
for name in ('pristine-preserved.sha256', 'pristine-sources.json', 'pristine-vadd-evidence.txt'):
    path = pristine_run.parents[1] / 'reports' / name
    if path.exists(): evidence['pristine/historical-identity/' + name] = path
for path in pristine_run.rglob('*'):
    if path.is_file(): evidence['pristine/vadd/' + str(path.relative_to(pristine_run))] = path

# Preserve the exact sessions shown in the videos as well as the earlier full
# acceptance. A video recheck must not silently borrow another run's raw log.
stage1_text = re.sub(r'\x1b\[[0-9;]*m', '', (videos[0] / 'terminal.log').read_text(errors='replace'))
stage1_candidates = {Path(line.strip()) for line in stage1_text.splitlines()
                     if re.fullmatch(re.escape(str(root / 'reports')) + r'/demo-stage1-\d{8}T\d{6}Z', line.strip())}
if len(stage1_candidates) != 1:
    raise SystemExit('Cannot identify the exact live session in the stage-one video')
stage1_session = stage1_candidates.pop()
if (stage1_session / 'exit-status.txt').read_text().strip() != '0':
    raise SystemExit('Stage-one live session did not complete successfully')
for path in stage1_session.rglob('*'):
    if path.is_file(): evidence['video-rechecks/stage1/' + str(path.relative_to(stage1_session))] = path
if (stage1_session / 'rtl-evidence.txt').exists():
    live = Path((stage1_session / 'rtl-evidence.txt').read_text().strip())
    if (live / 'exit-status.txt').read_text().strip() != '0':
        raise SystemExit('Stage-one live RTL run failed')
    for path in live.rglob('*'):
        if path.is_file(): evidence['video-rechecks/stage1/rtl/' + str(path.relative_to(live))] = path
for label in ('smoke', 'register'):
    log = acceptance_path / ('video-stage2-' + label + '.log')
    folders = [Path(s.removeprefix('RTL evidence: ')) for s in log.read_text().splitlines()
               if s.startswith('RTL evidence: ')]
    if len(folders) != 1 or (folders[0] / 'exit-status.txt').read_text().strip() != '0':
        raise SystemExit('Stage-two live session is missing: ' + label)
    for path in folders[0].rglob('*'):
        if path.is_file(): evidence['video-rechecks/stage2/' + label + '/' + str(path.relative_to(folders[0]))] = path
stage3_log = acceptance_path / 'video-stage3-fault.log'
stage3_folders = [Path(s.removeprefix('Fault-check evidence: ')) for s in stage3_log.read_text().splitlines()
                  if s.startswith('Fault-check evidence: ')]
if len(stage3_folders) != 1 or 'FAULT_CHECK_PASS' not in stage3_log.read_text():
    raise SystemExit('Stage-three live fault-check session is missing')
stage3_fault = stage3_folders[0]
for path in stage3_fault.rglob('*'):
    if path.is_file(): evidence['video-rechecks/stage3/fault-check/' + str(path.relative_to(stage3_fault))] = path
for label in ('positive-before', 'negative', 'positive-restored'):
    log = stage3_fault / (label + '.log')
    folders = [Path(s.removeprefix('RTL evidence: ')) for s in log.read_text().splitlines()
               if s.startswith('RTL evidence: ')]
    if len(folders) != 1:
        raise SystemExit('Missing live stage-three run: ' + label)
    for path in folders[0].rglob('*'):
        if path.is_file(): evidence['video-rechecks/stage3/' + label + '/' + str(path.relative_to(folders[0]))] = path
for report in (tested_root / 'reports').glob('vdot-build-*'):
    if not report.is_dir(): continue
    for path in report.rglob('*'):
        if path.is_file(): evidence['build-history/' + report.name + '/' + str(path.relative_to(report))] = path
completed_build = tested_root / binding['generated_rtl']['build_report']
for report in [completed_build, *(tested_root / 'reports').glob('model-resume-*'),
               *(tested_root / 'reports').glob('model-native-swap-*')]:
    if not report.is_dir(): continue
    for path in report.rglob('*'):
        if path.is_file(): evidence['build-history/' + report.name + '/' + str(path.relative_to(report))] = path
if args.optimization_dir:
    directory = args.optimization_dir.resolve(strict=True)
    performance = json.loads((directory / 'evidence.json').read_text())
    if performance['status'] != 'verified' or not performance['ab_inputs_identical']:
        raise SystemExit('Optimization A/B inputs were not verified')
    for path in directory.rglob('*'):
        if path.is_file(): evidence['optimization/report/' + str(path.relative_to(directory))] = path
    for phase, kinds in performance['runs'].items():
        for kind, item in kinds.items():
            run = Path(item['directory'])
            for path in run.rglob('*'):
                if path.is_file(): evidence[f'optimization/raw/{phase}/{kind}/' + str(path.relative_to(run))] = path
if args.reproduction_status:
    status_path = args.reproduction_status.resolve(strict=True)
    reproduction = json.loads(status_path.read_text())
    if reproduction['status'] != 'passed' or Path(reproduction['acceptance']).resolve() != (acceptance_path / 'acceptance.json').resolve():
        raise SystemExit('Clean reproduction does not identify this completed acceptance')
    for label, directory in [('completion', status_path.parent),
                             ('initial-attempt', tested_root / 'reports/independent-reproduction-20261106')]:
        for path in directory.rglob('*'):
            if path.is_file(): evidence['clean-reproduction/' + label + '/' + str(path.relative_to(directory))] = path
    for name in ('preparation.json', 'pristine-source.json', 'patched-source.json', 'firtool-file-heap.sh',
                 'depth12-stopped-for-selective-trace.json'):
        path = tested_root / 'reports' / name
        if path.exists(): evidence['clean-reproduction/preparation/' + name] = path
for path in (tested_root / 'reports/extension-preparation').rglob('*'):
    if path.is_file(): evidence['extension-preparation/' + str(path.relative_to(tested_root/'reports/extension-preparation'))] = path
for name in ('prepare-clean-20261105.sh', 'clean-prepare-driver.log', 'pristine-build-driver.log',
             'pristine-build-retry-driver.log', 'pristine-build-heap2g-driver.log',
             'pristine-resume-driver.log', 'pristine-validation-driver.log',
             'prepare-extension-clean-20261105.sh', 'extension-clean-driver.log',
             'queue-extension-acceptance-20261105.sh', 'extension-acceptance-driver.log',
             'queue-final-artifacts-20261105.sh', 'final-artifact-queue-inputs.sha256',
             'final-artifact-preparation-driver.log'):
    path = root / 'reports' / name
    if path.exists(): evidence['operation-logs/' + name] = path
for name in ('prepare-reproduction-20261106.py', 'reproduction-20261106-prepare.log',
             'reproduce-final-20261106.py', 'recover-reproduction-swap-20261106.py',
             'recover-reproduction-swap-j4-20261106.py',
             'reproduction-swap-20261106-driver.log', 'reproduction-swap-j4-20261106-driver.log',
             'temporary-swap-receipt.json', 'memory-user-terminal-20261106.log',
             'required-trace-depth-audit.json', 'trace-depth-probe.json',
             'independent-rtl-comparison-20261106.json', 'independent-before-after-rtl-20261106.json',
             'required-trace-signals-verified-20261106.json',
             'firtool-helper-provenance-20261106.json', 'official-question-state-20261106.json',
             'official-question-issue-20261106.json', 'official-question-comments-20261106.json',
             'official-question-final-check-20261106.json', 'official-question-comments-final-20261106.json',
             'reproduction-report-replay-verified-20261106.json'):
    path = root / 'reports' / name
    if path.exists(): evidence['operation-logs/' + name] = path
source = {name: root / name for name in binding['tracked_file_sha256']}
# The document category itself carries the full deployment/build text logs.
# Large raw FST and complete regression records remain in the evidence category.
document_log_prefixes = ('operation-logs/', 'build-history/', 'clean-reproduction/preparation/',
                         'clean-reproduction/initial-attempt/', 'pristine/', 'rtl/vadd/')
for relative, path in evidence.items():
    if relative.startswith(document_log_prefixes) and path.suffix in ('.log', '.txt', '.json', '.sha256', '.py', '.sh'):
        pdfs['deployment-and-operation-logs/' + relative] = path
packages = [archive('technical-documents.zip', pdfs),
            archive('demonstration-videos.zip', video_files),
            archive('supporting-evidence.zip', evidence),
            archive('source-and-reproduction.zip', source)]
result = {'status': 'packaged_not_uploaded', 'project_title': '香山向量点积指令设计',
          'team': '全栈漏洞队', 'final_project_head': head, 'packages': packages,
          'source_publication': 'source tree only; supporting-evidence.zip may contain local environment output and is for the official portal'}
(destination / 'packages-manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
(destination / 'SHA256SUMS').write_text('\n'.join(p['sha256'] + '  ' + Path(p['file']).name for p in packages) + '\n')
print('SUBMISSION_PACKAGES_VERIFIED', destination)
