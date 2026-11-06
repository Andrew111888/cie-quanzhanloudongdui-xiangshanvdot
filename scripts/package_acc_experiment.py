"""Assemble a source-bound accumulating-dot experiment without portal actions."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--receipt',type=Path,required=True)
parser.add_argument('--pdf',type=Path,default=Path('output/pdf/累加融合实验报告.pdf'))
parser.add_argument('--output',type=Path,default=Path('output/累加融合实验'))
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
receipt = json.loads(args.receipt.read_text())
assert receipt['status'] == 'passed'
for name,value in receipt['evidence_sha256'].items():
    assert digest(Path(name)) == value,name
pdf = args.pdf.resolve(strict=True)
pdf_review = json.loads(pdf.with_suffix('.json').read_text())
assert pdf_review['status'] == 'verified' and pdf_review['sha256'] == digest(pdf)
assert pdf_review['metadata'] == {'/Author':'全栈漏洞队'}
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=root,text=True).strip(), 'Commit the final source and documentation first'
head = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
out = args.output.resolve()
out.mkdir(parents=True,exist_ok=False)
copied = {}
def copy_file(source,relative):
    source=source.resolve(strict=True)
    target=out/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
    assert digest(source)==digest(target)
    copied[str(source)]={'package_path':str(relative),'sha256':digest(target)}
def copy_tree(source,relative):
    for path in sorted(source.rglob('*')):
        if path.is_file():
            copy_file(path,Path(relative)/path.relative_to(source))
copy_file(pdf,Path('报告')/pdf.name)
copy_file(pdf.with_suffix('.json'),Path('报告')/pdf.with_suffix('.json').name)
copy_file(args.receipt,Path('证据/总验收回执.json'))
copy_tree(root/'docs/data/acc-results',Path('证据/整核'))
copy_tree(root/'docs/data/acc-ppa',Path('证据/模块对照索引'))
copy_tree(Path(receipt['ppa_directory']),Path('证据/实际整核模块PPA'))
copy_tree(Path(receipt['build_report']),Path('证据/整核构建'))
for name,directory in receipt['regressions'].items():
    copy_tree(Path(directory),Path('证据/原指令回归')/name)
if receipt.get('precedence_directory'):
    copy_tree(Path(receipt['precedence_directory']),Path('证据/异常优先级'))
if receipt.get('reference_correction_directory'):
    copy_tree(Path(receipt['reference_correction_directory']),Path('证据/参考修正构建'))
if receipt.get('corrected_reference_legal_directory'):
    copy_tree(Path(receipt['corrected_reference_legal_directory']),Path('证据/修正参考合法输入'))
copy_file(root/'docs/累加融合录屏要点.md',Path('录屏要点.md'))
copy_tree(root/'experiments/acc/generated',Path('源码/实际源码与RTL'))
for name in ['xiangshan.patch','nemu.patch']:
    copy_file(root/'patches'/name,Path('源码/补丁')/name)
for source in [root/'contract.json',root/'experiments/acc/contract.json']:
    copy_file(source,Path('源码/契约')/('原点积.json' if source.parent==root else '累加点积.json'))
copy_file(root/'LICENSE',Path('源码/LICENSE'))
copy_file(root/'NOTICE.md',Path('源码/NOTICE.md'))
archive=out/'源码/项目源码.tar.gz'
subprocess.run(['git','archive','--format=tar.gz','--output='+str(archive),head],cwd=root,check=True)
frozen=Path(receipt['build_report']).parents[1]
bundle_records=[]
for name,repo,base,expected in [
    ('香山扩展',frozen/'third_party/XiangShan','7b16188f7f18a97be69c9b1a2dae8a446eec3b47',receipt['core_commit']),
    ('NEMU扩展',root/'build/acc-nemu-precedence/NEMU','d772a9d9e06f663d529bd1c6518480c1ee59ded2',receipt.get('corrected_nemu_commit',receipt['nemu_commit'])),
]:
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()==expected
    target=out/'源码'/(name+'.bundle')
    subprocess.run(['git','bundle','create',str(target),'HEAD','^'+base],cwd=repo,check=True,stdout=subprocess.DEVNULL)
    checked=subprocess.run(['git','bundle','verify',str(target)],cwd=repo,check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/'源码'/(name+'校验.txt')).write_text(checked.stdout)
    bundle_records.append({'file':str(target.relative_to(out)),'base_commit':base,'head_commit':expected,'sha256':digest(target)})
binding={'status':'verified','final_project_commit':head,'core_build_project_commit':receipt['build_project_head'],'core_commit':receipt['core_commit'],'initial_nemu_commit':receipt['nemu_commit'],'corrected_nemu_commit':receipt.get('corrected_nemu_commit'),'source_archive_sha256':digest(archive),'evidence_receipt_sha256':digest(args.receipt),'pdf_sha256':digest(pdf),'copied_sources':copied,'extension_bundles':bundle_records,'official_portal_updated':False,'baseline_project_changed':False,'videos_included':False}
(out/'源码与证据绑定.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n')
(out/'README.md').write_text('''# 累加融合实验交付包

本包在原vdot赛题实现之外增加vdot.acc，包含实际整核实现、功能差分、强RVV长点积与单/多累加链对照，以及算术模块资源和时序数据。原三阶段作品材料保留在原项目；本包是独立实验成果。

- 报告/：中文PDF，作者为全栈漏洞队，页脚仅居中页码。
- 源码/：完整项目源码归档、相对固定上游的补丁、实际生成RTL、完整修改文件、契约与两个增量Git bundle。
- 证据/：整核构建、1000组唯一随机输入、180条性能样本、流水/边界寄存器/故障恢复、异常优先级修正和同约束PPA原始数据。
- 录屏要点.md：供参赛者自行录屏的入口和讲解顺序。

解开源码/项目源码.tar.gz后，按docs/累加融合复现.md准备固定上游和工具。增量bundle需先获取对应固定上游base提交，再导入HEAD；无需依赖作品仓库内保存完整上游历史。源码与证据绑定.json分别记录硬件构建源码、初始参考、异常修正参考及最终文档源码。性能周期取实际RTL，NEMU独立运行仅用作功能核对。文件中的原始绝对路径保留实验现场身份，包内位置由copied_sources映射。

算术模块面积为Liberty属性单位，布局前STA采用理想时钟和零互连；这些数据不表示全核频率或功耗。独立分片各自预热，不能视为完全相同的缓存初态。

本包不含录屏或PPT，未执行官网上传，也未替换原作品的正式提交材料。
''')
files={str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file()}
(out/'文件校验.json').write_text(json.dumps({'status':'verified','files_sha256':files},ensure_ascii=False,indent=2)+'\n')
(out/'SHA256SUMS').write_text(''.join(f'{value}  {name}\n' for name,value in files.items()))
archive=out.with_suffix('.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for path in sorted(out.rglob('*')):
        if path.is_file():z.write(path,Path(out.name)/path.relative_to(out))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name,value in files.items():assert hashlib.sha256(z.read(str(Path(out.name)/name))).hexdigest()==value,name
summary={'status':'verified','directory':str(out),'archive':str(archive),'archive_sha256':digest(archive),'final_project_commit':head,'file_count':len(list(out.rglob('*'))),'file_hashes_verified':len(files),'zip_crc_verified':True}
archive.with_suffix('.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False))
