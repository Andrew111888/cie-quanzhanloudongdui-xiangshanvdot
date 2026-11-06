"""Export generated RTL from a completed full-core build with its provenance."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('build_report', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
report = args.build_report.resolve(strict=True)
tested_root = report.parents[1]
source = json.loads((report / 'source-after.json').read_text())
version = re.search(r'firtool-([0-9.]+)', (report / 'firtool-version.txt').read_text())
if version is None:
    raise SystemExit('Missing recorded firtool version')
if (report / 'compile-exit-status.txt').read_text().strip() != '0':
    raise SystemExit('The full-core build did not complete')
subprocess.run(['sha256sum', '--check', str(report / 'emu.sha256')],
               cwd=tested_root / 'third_party/XiangShan', check=True)


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


fir = tested_root / 'third_party/XiangShan/build/rtl/SimTop.fir'
if digest(fir) != (report / 'fir.sha256').read_text().split()[0]:
    raise SystemExit('The generated FIR changed after the build')
original_patch = tested_root / 'patches/xiangshan.patch'
if digest(root / 'patches/xiangshan.patch') != digest(original_patch):
    raise SystemExit('The destination uses another processor patch')
has_accumulator = (fir.parent / 'VdotAccRetimedDatapath.sv').is_file()
output = root / 'rtl' if has_accumulator else root / 'rtl/baseline'
arithmetic = 'VdotAccRetimedDatapath.sv' if has_accumulator else 'VdotDatapath.sv'
verified = None
if has_accumulator:
    verified = json.loads((root / 'configs/source-manifest.json').read_text())
    if verified['tested']['XiangShan'] != source['repositories']['XiangShan']['head']:
        raise SystemExit('Update the verified source snapshot for this core before exporting')
    for name in (arithmetic, 'VIMacU.sv'):
        if digest(fir.parent / name) != verified['rtl']['rtl/' + name]:
            raise SystemExit('Generated RTL differs from the verified arithmetic output: ' + name)
output.mkdir(parents=True, exist_ok=True)
modules = []
for name in (arithmetic, 'VIMacU.sv'):
    original = fir.parent / name
    target = output / name
    shutil.copyfile(original, target)
    if digest(original) != digest(target):
        raise SystemExit('Generated module copy differs: ' + name)
    modules.append({'file': name, 'generated_path': str(original.relative_to(tested_root)),
                    'sha256': digest(target)})
manifest = {'schema': 'generated-rtl/v1', 'build_status': 'completed',
            'tested_project_head': source['project_head'],
            'upstream_xiangshan_head': source['repositories']['XiangShan']['head'],
            'firtool': version[1], 'build_report': str(report.relative_to(tested_root)),
            'fir_sha256': digest(fir), 'xiangshan_patch_sha256': digest(original_patch),
            'modules': modules}
if has_accumulator:
    manifest.update(schema='generated-rtl/v2', xiangshan_head=verified['tested']['XiangShan'],
                    initial_nemu_head=verified['tested']['NEMU_initial'],
                    corrected_nemu_head=verified['tested']['NEMU_corrected'],
                    nemu_patch_sha256=digest(root / 'patches/nemu.patch'),
                    baseline_directory='baseline',
                    source_manifest='../configs/source-manifest.json')
(output / 'provenance.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('GENERATED_RTL_EXPORTED', output)
