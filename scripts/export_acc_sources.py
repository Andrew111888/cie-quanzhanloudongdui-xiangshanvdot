"""Export the exact generated module and patched source files from a core build."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--build-report', type=Path, required=True)
parser.add_argument('--corrected-reference', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
build_report = args.build_report.resolve(strict=True)
core = build_report.parents[1]
source = json.loads((build_report/'source-after.json').read_text())
correction = json.loads(args.corrected_reference.read_text())
assert correction['status'] == 'passed'
destination = root/'experiments/acc/generated'
destination.mkdir(exist_ok=False)
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
mapping = {}
def copy(path, relative):
    target = destination/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    assert digest(path) == digest(target)
    mapping[str(relative)] = {'sha256': digest(target), 'original': str(path.resolve())}
for repo, patch in [('XiangShan','xiangshan.patch'),('NEMU','nemu.patch')]:
    repository = core/'third_party'/repo
    if repo == 'NEMU':
        repository = root/'build/acc-nemu-precedence/NEMU'
        expected = correction['corrected_nemu_commit']
    else:
        expected = source['repositories'][repo]['head']
    head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=repository,text=True).strip()
    assert head == expected
    assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=repository,text=True).strip()
    for name in re.findall(r'^\+\+\+ b/(.*)$',(root/'patches'/patch).read_text(),re.M):
        copy(repository/name,Path(repo)/name)
for name in ['VdotAccRetimedDatapath.sv','VIMacU.sv']:
    copy(core/'third_party/XiangShan/build/rtl'/name,Path('rtl')/name)
record = {
    'scope': 'actual full-core generated arithmetic module and wrapper, with complete modified Chisel/NEMU source files',
    'core_build_project_commit': source['project_head'],
    'core_commit': source['repositories']['XiangShan']['head'],
    'initial_reference_commit': source['repositories']['NEMU']['head'],
    'corrected_reference_commit': correction['corrected_nemu_commit'],
    'files': mapping,
    'wrapper_requires_existing_core_dependencies': True,
    'arithmetic_module_is_the_actual_full_core_output': True,
}
(destination/'provenance.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
(destination/'README.md').write_text('''# 实际整核源码与RTL

rtl/VdotAccRetimedDatapath.sv为独立整核构建生成的实际算术模块，rtl/VIMacU.sv为同次构建的执行单元包装器。包装器依赖该固定版本其余向量模块，不能单独代替整核。上游许可证与文件声明继续适用。

XiangShan保存本轮修改的五个完整Chisel源码文件，NEMU保存含异常优先级修正的五个完整源码文件；完整上游工程由固定版本及patches补丁获取。provenance.json分别记录硬件构建、初始参考、修正参考身份与逐文件摘要。
''')
print(destination)
