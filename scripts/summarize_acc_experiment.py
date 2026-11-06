"""Bind completed core, functional, fault and performance evidence to a report."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess

parser=argparse.ArgumentParser()
for name in ('build-report','validation','benchmark','pipeline','registers','fault','ppa','driver-record','precedence','reference-correction','corrected-reference-legal'):
    parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
evidence={}
def bind(path):
    path=path.resolve(strict=True);evidence[str(path)]=digest(path)
def result(directory):
    path=directory/'results.json';r=read(path);assert r['status']=='passed',str(directory);bind(path)
    for name,value in r.get('input_sha256',{}).items():assert digest(Path(name))==value,name
    return r
val=result(args.validation);bench=result(args.benchmark);pipe=result(args.pipeline);registers=result(args.registers);fault=result(args.fault)
precedence=result(args.precedence);corrected_legal=result(args.corrected_reference_legal)
assert precedence['scope']=='real_rtl_nemu_decode_fault_precedence'
assert precedence['case_count']==48 and precedence['original_nemu_wrong_cases']==20
assert precedence['original_reference_rtl_mismatch_observed'] and precedence['corrected_reference_rtl_all_cases_passed']
assert corrected_legal['scope']=='nemu_standalone' and corrected_legal['random_input_groups']==1000
correction=read(args.reference_correction/'results.json');assert correction['status']=='passed'
assert digest(root/'patches/nemu.patch')==correction['patch_sha256']
for item in correction['outputs'].values():assert digest(Path(item['path']))==item['sha256']
ref_item=correction['outputs']['reference']
assert bench['input_sha256'][str(Path(ref_item['path']).resolve())]==ref_item['sha256']
assert val['scope']=='rtl_nemu_difftest' and val['reported_core_dirty']==0
assert bench['difftest_enabled'] and bench['reported_core_dirty']==0
assert bench['long_sample_count']==60 and bench['chain_sample_count']==120
assert pipe['scope']==registers['scope']=='rtl_nemu_difftest'
assert fault['scope']=='real_rtl_nemu_acc_fault_and_restore'
before=read(args.build_report/'source-before.json');after=read(args.build_report/'source-after.json')
assert before['repositories']==after['repositories'] and before['project_files_sha256']==after['project_files_sha256']
for stage in ('chisel','firtool','compile'):assert (args.build_report/(stage+'-exit-status.txt')).read_text().strip()=='0'
core=args.build_report.parents[1];core_commit=after['repositories']['XiangShan']['head']
assert core_commit.startswith(val['reported_core_commit_prefix']) and core_commit.startswith(bench['reported_core_commit_prefix'])
assert not after['repositories']['XiangShan']['status'] and not after['repositories']['NEMU']['status']
ppa=read(args.ppa/'results.json');assert ppa['status']=='passed';bind(args.ppa/'results.json')
chosen=next(x for x in ppa['results'] if x['design']=='chisel_retimed')
baseline=next(x for x in ppa['results'] if x['design']=='original')
full_module=core/'third_party/XiangShan/build/rtl/VdotAccRetimedDatapath.sv'
assert digest(full_module)==digest(args.ppa/'inputs/VdotAccRetimedDatapath.sv');bind(full_module)
for name in ('patches/xiangshan.patch','contract.json'):
    assert digest(root/name)==after['project_files_sha256'][name],name
# The only post-build reference correction inserts decoder legality checks
# before the pre-existing configuration/arithmetic body. Preserve the original
# reference identity for all completed random and performance runs.
old_nemu=core/'third_party/NEMU';new_nemu=root/'build/acc-nemu-precedence/NEMU'
assert correction['original_nemu_commit']==after['repositories']['NEMU']['head']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=new_nemu,text=True).strip()==correction['corrected_nemu_commit']
changed=subprocess.check_output(['git','diff','--name-only',correction['original_nemu_commit'],'HEAD'],cwd=new_nemu,text=True).splitlines()
assert changed==['src/isa/riscv64/instr/rvv/vcompute.h'],changed
old_body=(old_nemu/'src/isa/riscv64/instr/rvv/vcompute.h').read_text()
new_body=(new_nemu/'src/isa/riscv64/instr/rvv/vcompute.h').read_text()
begin=new_body.index('  /* Mirror the existing vector decoder')
end=new_body.index('  if (VLEN != 128',begin)
assert new_body[:begin]+new_body[end:]==old_body
assert digest(core/'patches/nemu.patch')==after['project_files_sha256']['patches/nemu.patch']
for path in [old_nemu/'src/isa/riscv64/instr/rvv/vcompute.h',new_nemu/'src/isa/riscv64/instr/rvv/vcompute.h',root/'patches/nemu.patch']:
    bind(path)
regressions={}
for name in ('vadd_test','vdot_smoke','register_test','pipeline_test'):
    lines=(args.driver_record/('regression-'+name+'.log')).read_text().splitlines()
    directory=Path(next(s.removeprefix('RTL evidence: ') for s in lines if s.startswith('RTL evidence: ')))
    text=(directory/'run.log').read_text();assert (directory/'exit-status.txt').read_text().strip()=='0'
    assert 'HIT GOOD TRAP' in text and 'Difftest enabled.' in text and 'dirty: 0' in text
    regressions[name]=str(directory)
    for p in directory.iterdir():
        if p.is_file():bind(p)
for directory in (args.validation,args.benchmark,args.pipeline,args.registers,args.fault,args.build_report,args.precedence,args.reference_correction,args.corrected_reference_legal):
    for p in directory.rglob('*'):
        if p.is_file() and p.suffix not in {'.o','.a'}:bind(p)
for p in args.ppa.rglob('*'):
    if p.is_file():bind(p)
unit_log=root/'reports/acc-preparation/chisel-unit-retimed.log'
unit_text=re.sub(r'\x1b\[[0-9;]*m','',unit_log.read_text())
assert 'Tests: succeeded 5, failed 0' in unit_text and 'All tests passed.' in unit_text
bind(unit_log)
auxiliary={}
for filename in ('compact-layout-audit.json','compact-parser-checks.json'):
    path=root/'reports/acc-preparation'/filename
    record=read(path);assert record['status']=='passed';bind(path);auxiliary[filename]=path
layout=read(auxiliary['compact-layout-audit.json'])
assert layout['all_12_function_pcs_equal_across_shards'] and layout['all_arrays_64byte_aligned']
for row in layout['rows']:
    assert digest(args.benchmark/row['part']/'test.elf')==row['elf_sha256']
args.output.mkdir(parents=True,exist_ok=False)
public=root/'docs/data/acc-results';public.mkdir(exist_ok=False)
for group,directory in [('validation',args.validation),('benchmark',args.benchmark),('pipeline',args.pipeline),('registers',args.registers),('fault',args.fault),('precedence',args.precedence),('corrected-reference-legal',args.corrected_reference_legal)]:
    for p in directory.rglob('*'):
        if p.is_file():q=public/group/p.relative_to(directory);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
(public/'unit').mkdir();shutil.copy2(unit_log,public/'unit/chisel.log')
for filename,path in auxiliary.items():shutil.copy2(path,public/'unit'/filename)
chain_increment=[]
for count in (1,2,4,8):
    pair={}
    for variant in (0,1):
        rows={r['rounds']:r for r in bench['chain_summary'] if r['chains']==count and r['variant']==variant}
        pair[variant]=(rows[512]['median_cycles']-rows[128]['median_cycles'])/(384*count)
    chain_increment.append({'chains':count,'explicit_fragment_increment_cycles_per_dot':pair[0],'fused_fragment_increment_cycles_per_dot':pair[1]})
receipt={'status':'passed','build_project_head':before['project_head'],'core_commit':core_commit,'nemu_commit':after['repositories']['NEMU']['head'],'build_report':str(args.build_report.resolve()),'regressions':regressions,'validation_directory':str(args.validation.resolve()),'benchmark_directory':str(args.benchmark.resolve()),'pipeline_directory':str(args.pipeline.resolve()),'registers_directory':str(args.registers.resolve()),'fault_directory':str(args.fault.resolve()),'ppa_directory':str(args.ppa.resolve()),'functional_instruction_executions':val['legal_instruction_executions'],'pipeline_acc_instructions':pipe['acc_instructions'],'long_samples':bench['long_sample_count'],'chain_samples':bench['chain_sample_count'],'long_comparisons':bench['long_comparisons'],'chain_comparisons':bench['chain_comparisons'],'chain_increment_estimates':chain_increment,'mapped_arithmetic_area':chosen['total_area_library_units'],'mapped_original_area':baseline['total_area_library_units'],'mapped_area_increase_percent':100*(chosen['total_area_library_units']/baseline['total_area_library_units']-1),'full_core_generated_module_sha256':digest(full_module),'timing':chosen['timing'],'evidence_sha256':evidence,'official_portal_updated':False,'published_baseline_submission_changed':False,'videos_provided':False}
receipt.update({'corrected_nemu_commit':correction['corrected_nemu_commit'],'precedence_directory':str(args.precedence.resolve()),'reference_correction_directory':str(args.reference_correction.resolve()),'corrected_reference_legal_directory':str(args.corrected_reference_legal.resolve()),'reference_change_arithmetic_and_late_config_body_unchanged':True,'random_reference':'initial reference','performance_reference':'corrected reference; also tested for all 48 precedence cases and 1000 random input groups'})
(args.output/'results.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
def value(rows,variant,k):return next(r for r in rows if r['variant']==variant and r['k']==k)
def number(row):return f"{row['median_cycles']:.0f}（{row['min_cycles']}-{row['max_cycles']}）"
long_lines=[]
for k in (32,128,512):
    rows=[value(bench['long_summary'],v,k) for v in range(4)];cmp=next(x for x in bench['long_comparisons'] if x['k']==k)
    long_lines.append('| '+str(k)+' | '+' | '.join(number(x) for x in rows)+f" | {cmp['rvv_over_acc']:.3f} |")
chain_lines=[]
for count in (1,2,4,8):
    cmp=next(x for x in bench['chain_comparisons'] if x['chains']==count and x['rounds']==512);inc=next(x for x in chain_increment if x['chains']==count)
    chain_lines.append(f"| {count} | {cmp['dot_plus_add_median']} | {cmp['acc_median']} | {cmp['dot_plus_add_over_acc']:.3f} | {inc['fused_fragment_increment_cycles_per_dot']:.3f} |")
timing=next(x for x in chosen['timing'] if x['clock_period_ns']==1.5)
body=f'''# 累加融合实验报告

香山昆明湖V2向量点积扩展。队伍：全栈漏洞队。参赛单位：西安电子科技大学。

## 一、设计目标与语义

在原有8项点积之外新增vdot.acc，保留原vdot的不累加语义。累加版将旧目标低32位作为真实输入，计算模2^32的融合累加，目标高96位清零。支持SEW=8、VLEN=128、LMUL=1、VL=8、vstart=0、vm=1；两源高64位不参与计算。

```text
partial = sum(signed8(vs1[i]) * signed8(vs2[i]), i=0..7)
vd.low32 = (old_vd.low32 + partial) mod 2^32
vd.high96 = 0
```

新编码mask/match为0xfc00707f/0x0400000b，内部操作类型0x101。译码保留第三源，并设置isDependOldVd，防止TA及完整覆盖条件误删真实累加依赖。操作数读取、ROB、有效位、写回、异常和冲刷沿用现有向量通路；与向量乘法共享执行位置。非法配置保持原目的和vstart，异常行为与原点积契约一致。

## 二、两级压缩重定时

![两级累加融合数据通路](figures/acc-retimed-datapath.svg)

8路乘法器由两种点积指令共用，普通vdot选择累加输入零。第一阶段完成乘法、符号扩展和第一层3:2压缩，寄存6项和/进位；第二阶段继续压缩至两项，经32位并行前缀加法寄存输出。各层按模2^32截断，不串接独立的最终累加加法器。

该结构在保持两个有效使能边沿延迟和一拍接收间隔的条件下，重新分配两级组合逻辑。四种累加Chisel结构及原模块测试均通过；完整原型/实际RTL黄金验证含12类定向、4096组随机及独立使能保持，每模型检查8217拍完整128位结果。

## 三、同约束资源与时序

固定Nangate45 typical、1.10 V、25°C，ABC目标1000 ps，每设计只映射一次，同一网表分别检查1/1.5/2.5 ns。输入/输出延迟100 ps，输入转换50 ps，输出负载5 fF，不确定度20 ps，理想时钟、零互连。综合包装器把两级使能绑定为公共enable，完整FU控制与端口未计入面积；独立使能由功能测试另行覆盖。

| 结构 | 面积，Liberty属性单位 | 1.5 ns建立裕量，ns |
|---|---:|---:|
| 原始不累加模块 | 4944.408 | +0.351741 |
| 平衡归约后串累加，单元输出 | 5431.188 | -0.561671 |
| CSA及普通最终加法，单元输出 | 5733.896 | -0.220036 |
| CSA及并行前缀，单元输出 | 5830.188 | -0.055645 |
| 提前压缩及前缀，单元输出 | 5608.344 | +0.100698 |
| 提前压缩及前缀，整核实际输出 | {chosen['total_area_library_units']:.3f} | {timing['worst_setup_slack_ns']:+.6f} |

前五项为同轮结构对照，最后一项另绑定整核firtool优化后的实际SV并通过同样黄金检查。整核实际算术模块较原模块增加{receipt['mapped_area_increase_percent']:.3f}%映射面积，159个触发器；1 ns仍有负建立裕量。面积单位保留Liberty属性单位，不换算为物理面积；这些数据不代表全核频率或功耗。

## 四、整核功能与差分

从已提交的香山/NEMU扩展源码重新生成整核与参考库，模型自然打印dirty: 0。随机用例按全局序号拆成16片，保持原固定种子输入序列，逐片独立差分后检查1006个序号无遗漏、无重复。{val['legal_instruction_executions']}次合法点积覆盖1000组随机、6组定向、6种别名、TA/TU、正负溢出及源高位；每片另重复640条累加链和7种非法形式，重复项不增加唯一随机输入数量。非法配置检查目的及vstart保持，并核对各异常的预期mtval。额外1664条累加流水测试覆盖独立目的、vadd生产者、别名链及两个分支方向；v0/v31另有6形式、两种策略的整核差分。

原向量加法、点积smoke、寄存器及1664条流水四项回归均通过；标准向量乘法、归约与访存由本轮完整长点积的两条RVV路径覆盖。新增1000组随机同时覆盖原vdot对照，共2012次原指令执行。专用非零累加探针的正常结果为0x12345680，故障NEMU参考库给出0x12345681，真实Difftest报告v12_low差异；正常、故障、恢复原始退出码依次为0、1、0。没有跳过新指令，也没有用DUT结果覆盖参考状态。

交叉异常检查另覆盖原vdot与累加版各24种形式。旧参考在48例中有20例mtval错误，RTL差分检出首个差异；修正前置寄存器对齐及masked目的v0检查后，同一RTL与新参考48例全部通过，目标及vstart保持。修正参考另通过1000组固定随机输入的NEMU功能回归。整核随机及错误参考实验保留其初始参考库身份，完整性能采样使用修正参考；修正仅插入译码合法性检查，合法算术与晚期配置检查的源代码前后逐字节相同，两版参考分别保存摘要。

## 五、真实长点积

两源为相同连续int8数组，每条实现沿完整K维累加，末尾仅保存一次相同16字节结果。计时包含初始化、必要配置、全部加载、循环、跨块累加、末尾归并/归约、完整存储及结束fence；黄金计算在计时外。36个测量组分片运行，每组仍单独预热后重复5次，60条长点积及120条累加链样本均启用RTL/NEMU差分，组号无遗漏、无重复。测试程序每次检查完整128位和未用哨兵，紧凑日志保留每条链低32位及定向有序校验摘要，由Python独立重建核对；高位另外由程序检查及向量状态差分覆盖。下表为中位周期及范围，加速比分子取两条RVV候选较短的中位数。

| K | 原vdot+加法 | RVV8 | RVV16 | vdot.acc | 较快RVV/acc |
|---:|---|---|---|---|---:|
{chr(10).join(long_lines)}

四路径每32项循环指令数为28、28、16、22。融合路径消除4条显式向量加法及两次循环内配置切换，保留四个独立累加器。各分片的同名内核函数入口PC相同；输入数组基址可不同，两个源之间的512字节间距及64字节对齐保持一致，各组独立预热。指令数减少不等同于周期同比下降；与较强RVV16的结果按实际数值判断。

## 六、单链与多链

固定相同预加载输入和非零累加初值，比较原vdot+显式e32加法及融合路径。1/2/4/8链、32/128/512轮、五次重复共120条样本，均检查每条链的完整128位结果及未使用位置的哨兵。下表为512轮中位周期；增量估计为(C512-C128)/(384×链数)，包含循环和调度成本，不能称裸FU延迟。

| 独立链数 | 原vdot+加法周期 | 融合周期 | 原路径/融合 | 融合增量周期/点积 |
|---:|---:|---:|---:|---:|
{chr(10).join(chain_lines)}

![整核程序片段的实测周期比](figures/acc-fragment-ratios.png)

## 七、复现与交付

源码含Chisel完整补丁、实际生成RTL、NEMU扩展、功能/性能程序、黄金模型和运行入口。原始日志、命令、反汇编、逐次CSV、工具与输入摘要随实验包保存。复现入口见[累加融合复现](累加融合复现.md)，逐次结果见[实验数据索引](data/acc-results/README.md)。

本轮报告区分算术模块、整核程序片段和不同归约粒度。采用累加、压缩树和前缀加法等已有机制，工程改进集中在昆明湖V2的共享路径、跨级逻辑分配、真实依赖保护及可复现对照。
'''
(root/'docs/累加融合实验结果.md').write_text(body)
(public/'README.md').write_text(f'# 累加融合整核实验数据\n\n[实验报告](../../累加融合实验结果.md)、[复现入口](../../累加融合复现.md)。\n\nvalidation保存{val["legal_instruction_executions"]}次功能执行，包含1000组唯一随机输入；benchmark保存60条长点积及120条累加链样本，pipeline保存1664条流水测试，registers保存v0/v31别名，fault保存真实错误参考及恢复。每组均含输入快照、二进制、命令、原始日志与退出码；全部为实际RTL/NEMU证据。\n\n[长点积逐次样本](benchmark/long-samples.csv)、[链逐次样本](benchmark/chain-samples.csv)、[完整性能结果](benchmark/results.json)、[功能结果](validation/results.json)、[流水结果](pipeline/results.json)、[边界寄存器](registers/results.json)、[错误与恢复](fault/results.json)。\n')
(public/'package-manifest.json').write_text(json.dumps({'status':'verified','files_sha256':{str(p.relative_to(public)):digest(p) for p in sorted(public.rglob('*')) if p.is_file()}},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':'passed','receipt':str((args.output/'results.json').resolve()),'long_comparisons':bench['long_comparisons'],'chain_512':[r for r in bench['chain_comparisons'] if r['rounds']==512]},ensure_ascii=False))
