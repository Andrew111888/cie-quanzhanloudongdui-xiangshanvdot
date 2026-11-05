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
    return hashlib.sha256(path.read_bytes()).hexdigest()


fir = tested_root / 'third_party/XiangShan/build/rtl/SimTop.fir'
if digest(fir) != (report / 'fir.sha256').read_text().split()[0]:
    raise SystemExit('The generated FIR changed after the build')
original_patch = tested_root / 'patches/xiangshan.patch'
if digest(root / 'patches/xiangshan.patch') != digest(original_patch):
    raise SystemExit('The destination uses another processor patch')
output = root / 'rtl'
output.mkdir(exist_ok=True)
modules = []
for name in ('VdotDatapath.sv', 'VIMacU.sv'):
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
(output / 'provenance.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('GENERATED_RTL_EXPORTED', output)
