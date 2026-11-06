"""Package the numbered non-video deliverables without publishing anything."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

parser=argparse.ArgumentParser()
parser.add_argument('--binding',type=Path,required=True)
parser.add_argument('--pdf-dir',type=Path,required=True)
parser.add_argument('--basic-run',type=Path,required=True)
parser.add_argument('--stage1-evidence',type=Path,required=True)
parser.add_argument('--recorded-evidence-zip',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
binding=json.loads(args.binding.read_text())
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
assert binding['status']=='verified' and binding['final_project_head']==head
assert not subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip()
for name,value in binding['tracked_file_sha256'].items():assert digest(root/name)==value,name
pdfs=json.loads((args.pdf_dir/'reports-manifest.json').read_text())
assert pdfs['status']=='verified' and pdfs['final_project_head']==head
assert pdfs['binding_sha256']==digest(args.binding)
assert all(x['visual_review']=='passed' for x in pdfs['reports'])
basic=json.loads((args.basic_run/'cases.json').read_text())
assert basic['status']=='passed' and basic['source_unchanged']
assert digest(args.basic_run/'run.log')==basic['run_log_sha256']
basic_log=re.sub(r'\x1b\[[0-9;]*m','',(args.basic_run/'run.log').read_text())
stats=re.search(r'Core-0 instrCnt = ([0-9,]+), cycleCnt = ([0-9,]+)',basic_log)
assert stats is not None
basic_instructions,basic_cycles=(int(s.replace(',','')) for s in stats.groups())
old_recorded_digest='31066e24eb2d6ca15cfd298d836cc02718b78899878626a4949b9d5d6ea171f7'
assert digest(args.recorded_evidence_zip)==old_recorded_digest
out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
stages={1:out/'01-第一阶段',2:out/'02-第二阶段',3:out/'03-第三阶段'}
for p in stages.values():p.mkdir()
records=[]
def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    assert digest(src)==digest(dst)
    records.append({'source':str(src.resolve()),'copy':str(dst.relative_to(out)),'sha256':digest(dst)})
def tree(src,dst,exclude=()):
    for p in sorted(src.rglob('*')):
        if p.is_file() and not any(x in p.relative_to(src).parts for x in exclude):
            copy(p,dst/p.relative_to(src))

for item in pdfs['reports']:
    src=Path(item['file']);assert digest(src)==item['sha256']
    copy(src,stages[item['stage']]/src.name)
for n,p in stages.items():
    copy(args.binding,p/'source-binding.json')
    (p/'赛题条目对应.md').write_text(f'# 本阶段交付入口\n\n[完整赛题编号索引](源码与报告原稿/docs/SUBMISSION.md)\n\n[本阶段报告源稿](源码与报告原稿/docs/submission/stage{n}.md)\n\nPDF与原始证据位于本目录；源码和报告原稿保留完整的相对目录结构。\n')
    copy(args.pdf_dir/'reports-manifest.json',p/'reports-manifest.json')
tree(args.stage1_evidence/'1.1-environment-validation',stages[1]/'1.1-环境输出',exclude=('recording-origin','README.md'))
(stages[1]/'1.1-环境输出/README.md').write_text('# 1.1 实际环境输出\n\n[正式验收原始日志](acceptance-run/run.log)及[退出码](acceptance-run/exit-status.txt)。\n\n[既有真实终端画面](environment-output.png)对应另一份[复跑日志](recording-run/run.log)。两次来源分开保存；本包不含视频，官网录屏由参赛者另行完成。\n')
tree(args.stage1_evidence/'1.2-operation-logs',stages[1]/'1.2-部署操作日志',exclude=('reference-procedures','部署操作索引.md'))
log_index=(args.stage1_evidence/'1.2-operation-logs/部署操作索引.md').read_text().replace('reference-procedures/','../源码与报告原稿/docs/')
(stages[1]/'1.2-部署操作日志/部署操作索引.md').write_text(log_index)
tree(args.stage1_evidence/'1.3-vector-addition',stages[1]/'1.3-向量加法波形')
copy(root/'workloads/vadd_test.c',stages[1]/'1.1-环境输出/vadd_test.c')

tested=Path(binding['acceptance']).parents[1]
xs_paths=[
 'src/main/scala/xiangshan/backend/decode/VecDecoder.scala',
 'src/main/scala/xiangshan/backend/decode/isa/bitfield/RiscvInst.scala',
 'src/main/scala/xiangshan/backend/fu/vector/Vdot.scala',
 'src/main/scala/xiangshan/backend/fu/wrapper/VIMacU.scala',
]
for rel in xs_paths:
    copy(tested/'third_party/XiangShan'/rel,stages[2]/'2.2-RTL/Chisel'/rel)
for rel in ['patches/xiangshan.patch','rtl/VdotDatapath.sv','rtl/VIMacU.sv','rtl/provenance.json','datapath/test/src/VdotDatapathTest.scala']:
    copy(root/rel,stages[2]/'2.2-RTL'/rel)
for rel in ['examples/vdot_basic.c','scripts/run_basic_validation.sh','workloads/vdot_test.c','workloads/register_test.c','workloads/pipeline_test.c','tests/reference.py']:
    copy(root/rel,stages[2]/'2.3-基础测试/源码'/rel)
tree(args.basic_run,stages[2]/'2.3-基础测试/逐例整核运行')
for label in ('smoke','register','random','pipeline'):
    tree(Path(binding['rtl_runs'][label]['directory']),stages[2]/'2.3-基础测试/完整回归'/label)

nemu_source=json.loads((Path(binding['acceptance'])/'source-after.json').read_text())['repositories']['NEMU']['changed_source_sha256']
for rel,value in nemu_source.items():
    src=tested/'third_party/NEMU'/rel;assert digest(src)==value
    copy(src,stages[3]/'3.1-NEMU扩展/展开源码'/rel)
for rel in ['patches/nemu.patch','configs/nemu-reference.config','configs/nemu-standalone.config']:
    copy(root/rel,stages[3]/'3.1-NEMU扩展'/rel)
(stages[3]/'3.1-NEMU扩展/README.md').write_text('# NEMU扩展与差分说明\n\n补丁、配置和展开源码位于本目录。\n\n[完整差分说明](../源码与报告原稿/docs/DIFFTEST_CHECKS.md)\n')
for rel in ['workloads/vdot_test.c','workloads/benchmark.c','workloads/benchmark_rvv.c','workloads/dot_memory.c','workloads/latency_probe.c','scripts/performance_report.py','scripts/optimization_report.py']:
    copy(root/rel,stages[3]/'3.2-基线与测量源码'/rel)
tree(root/'docs/data/optimization',stages[3]/'3.3-性能分析/公开数据')
(stages[3]/'3.3-性能分析/README.md').write_text('# 性能分析入口\n\n[方法](../源码与报告原稿/docs/OPTIMIZATION.md)\n\n[优化结果](../源码与报告原稿/docs/OPTIMIZATION_RESULTS.md)\n\n[完整性能边界](../源码与报告原稿/docs/PERFORMANCE.md)\n\n本目录公开数据和同阶段原始协同与性能证据保留实测来源。\n')

archived=[]
with zipfile.ZipFile(args.recorded_evidence_zip) as z:
    for name in z.namelist():
        rel=Path(name)
        assert not rel.is_absolute() and '..' not in rel.parts
        if name.endswith('/') or 'video' in name:continue
        destinations=[]
        if name.startswith(('diagnostic/pipeline/','acceptance/pipeline-analysis/','acceptance/pipeline-events/','clean-reproduction/initial-attempt/datapath')):
            destinations.append(stages[2]/'扩展验证原始证据'/rel)
        if name.startswith(('fault-check/','fault-runs/','rtl/benchmark/','rtl/latency/','optimization/','acceptance/','diagnostic/pipeline/')):
            destinations.append(stages[3]/'原始协同与性能证据'/rel)
        if not destinations:continue
        payload=z.read(name)
        for dest in destinations:
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(payload)
            archived.append({'archive_member':name,'copy':str(dest.relative_to(out)),'sha256':digest(dest)})

tracked=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
contact=json.loads((root/'private/submission-contact.json').read_text())['contact_email'].encode()
source_files={}
for name in tracked:
    if not name:continue
    assert Path(name).parts[0] not in {'private','reports','output','third_party','tools','build','out','tmp'}
    payload=(root/name).read_bytes();assert contact not in payload,name
    source_files['源码/'+name]=root/name
    for stage in stages.values():
        copy(root/name,stage/'源码与报告原稿'/name)

offline_links=0
for stage in stages.values():
    for path in stage.rglob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(errors='replace')):
            if link.startswith(('http:','https:','#')):continue
            assert (path.parent/link.split('#')[0]).exists(),(str(path),link)
            offline_links+=1

def archive(path,files,readme):
    sums=[]
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name,p in sorted(files.items()):
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
            z.write(p,name);sums.append(digest(p)+'  '+name)
        z.writestr('阅读说明.txt',readme);sums.append(hashlib.sha256(readme.encode()).hexdigest()+'  阅读说明.txt')
        z.writestr('CONTENTS.sha256','\n'.join(sums)+'\n')
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        for line in z.read('CONTENTS.sha256').decode().splitlines():
            value,name=line.split('  ',1);assert hashlib.sha256(z.read(name)).hexdigest()==value
        assert not any(Path(name).suffix.lower() in {'.mp4','.mkv','.webm','.mov','.ppt','.pptx'} for name in z.namelist())
    return {'path':str(path),'sha256':digest(path),'bytes':path.stat().st_size}

packages=[]
for n,p in stages.items():
    local=[x for x in p.rglob('*') if x.is_file()]
    (p/'SHA256SUMS').write_text(''.join(digest(x)+'  '+str(x.relative_to(p))+'\n' for x in sorted(local)))
    packages.append(archive(out/(p.name+'-文档及证据.zip'),{str(x.relative_to(out)):x for x in p.rglob('*') if x.is_file()},
        f'全栈漏洞队；西安电子科技大学。第{n}阶段文档与原始证明。\n作品源码：{head}\n真实硬件构建/完整验收：{binding["tested_project_head"]}\n录屏由参赛者另行提供，本包不含视频。先读本阶段PDF及赛题条目对应.md。\n'))
packages.append(archive(out/'04-源码与复现.zip',source_files,f'全栈漏洞队；作品源码{head}。\n完整硬件实际构建为{binding["tested_project_head"]}；新增逐例验证另有输入与源码身份。\n代码入口见README.md、docs/SUBMISSION.md。官方仓库只接收公钥加密的提交信息，明文联系数据不在本包中。\n'))
copy(root/'docs/RECORDING_GUIDE.md',out/'录屏操作指南.md')
(out/'仓库地址.txt').write_text('https://github.com/Andrew111888/cie-quanzhanloudongdui-xiangshanvdot\n')
requirements=[]
for n,ids in {1:['1.1','1.2','1.3'],2:['2.1','2.2','2.3.1','2.3.2','2.3.3'],3:['3.1.1','3.1.2','3.2','3.3']}.items():
    for identifier in ids:requirements.append({'id':identifier,'stage':n,'status':'technical_materials_verified','directory':str(stages[n])})
manifest={'status':'non_video_materials_ready_videos_pending_portal_held','prepared_utc':datetime.now(timezone.utc).isoformat(),'final_project_head':head,'tested_project_head':binding['tested_project_head'],'basic_validation_source_head':basic['source_project_head'],'basic_validation_log_sha256':basic['run_log_sha256'],'source_binding_sha256':digest(args.binding),'requirements':requirements,'reports':pdfs['reports'],'packages':packages,'copied_source_records':records,'preserved_archive_source':{'path':str(args.recorded_evidence_zip),'sha256':old_recorded_digest},'extracted_records':archived,'videos':[{'stage':i,'status':'awaiting_participant_recording'} for i in (1,2,3)],'ppt':'deferred_by_participant','official_portal_updated':False,'official_pr_updated':False,'encryption':'pending_local_preparation'}
manifest['offline_markdown_links_checked']=offline_links
(out/'提交清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
readme=f'''# 参赛提交材料：按赛题要求

队伍：全栈漏洞队；参赛单位：西安电子科技大学。

非视频技术材料已准备；三段录屏由参赛者完成，当前未将视频标为已交付。官网暂停替换，本目录尚未上传官网；官方PR保持原版本。PPT按此前安排暂不制作。

| 官网位置 | 本地材料 | 配套证据 |
|---|---|---|
| 文档：第一阶段 | [一阶段执行日志](01-第一阶段/一阶段执行日志.pdf) | 1.1实际问候与IP；1.2完整225份记录及顺序索引 |
| 文档：第一阶段 | [一阶段过程文档](01-第一阶段/一阶段过程文档.pdf) | 1.3原始FST、参考文档与向量加法执行过程 |
| 文档：第二阶段 | [二阶段设计文档](02-第二阶段/二阶段设计文档.pdf) | 2.1设计；2.2展开Chisel、补丁、生成RTL |
| 文档：第二阶段 | [二阶段基础测试文档](02-第二阶段/二阶段基础测试文档.pdf) | 2.3正数、负数和边界值逐例输出及完整回归 |
| 文档：第三阶段 | [三阶段协同仿真文档](03-第三阶段/三阶段协同仿真文档.pdf) | 3.1 NEMU扩展、真实差分及故障反例 |
| 文档：第三阶段 | [三阶段性能分析文档](03-第三阶段/三阶段性能分析文档.pdf) | 3.2等价基线；3.3波形、周期、加速比和原始样本 |
| 代码仓库 | 仓库地址.txt | 04-源码与复现.zip可作代码附件；GitHub作品仓库为正式源码入口 |
| 视频：三阶段 | 待参赛者提供 | 录屏操作指南.md给出命令及讲解要点 |

每阶段有两份中文命名PDF，元数据仅保留作者“全栈漏洞队”，单位、最后修改人及其他Info/XMP字段均清除。每阶段另有“文档及证据.zip”，含两份PDF和原始证据，供系统接受ZIP时使用；系统只接受PDF时使用目录中的PDF，证据按平台允许的附件位置提供。

最终作品源码：{head}。真实完整硬件构建与验收：{binding['tested_project_head']}。新增逐例运行源码：{basic['source_project_head']}。关键处理器、NEMU、原有测试和配置逐字节相同；新增逐例演示是单独编译并真实执行的补充测试，不是一次新硬件构建。

六个基础用例逐项输出输入、期望、实际值和128位vd，实际运行{basic_instructions}条指令、{basic_cycles}周期，正常差分、GOOD TRAP、原始退出0。

尚未明确的指令结果宽度和支持范围仍按暂定契约披露。工程验证通过不代表赛题方确认或官方评审通过。

加密提交流程和PR模板另在“05-官方加密提交”准备；其中不放联系信息明文。现有PR继续使用同一条，不新建重复PR，不在公开正文添加作品地址、邮箱或性能流水账。

文件摘要见SHA256SUMS，各ZIP内部还有CONTENTS.sha256。机器条目和来源见提交清单.json。
'''
(out/'README.md').write_text(readme)
print(json.dumps({'directory':str(out),'requirements':len(requirements),'packages':packages,'videos':'pending_participant','portal':'held'},ensure_ascii=False,indent=2))
